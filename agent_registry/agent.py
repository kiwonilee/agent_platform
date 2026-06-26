import os
import httpx
import google.auth

from google.auth.transport.requests import Request
from google.adk.integrations.agent_registry import AgentRegistry
from google.adk.agents.llm_agent import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.tools.base_toolset import BaseToolset

from google.genai import types
from google.adk.apps import App
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# https://docs.cloud.google.com/agent-registry/authenticate-toolsets#auth-mcp
class GoogleAuth(httpx.Auth):
    def __init__(self):
        self.creds, _ = google.auth.default()
    def auth_flow(self, request):
        if not self.creds.valid:
            self.creds.refresh(Request())
        request.headers["Authorization"] = f"Bearer {self.creds.token}"
        yield request

# Initialize the registry client
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")

# Initialize the client
registry = AgentRegistry(
    project_id=project_id,
    location=location,
)

# Retrieve an MCP toolset using its resource name in short or full format
mcp_server_name = "mcpServers/agentregistry-00000000-0000-0000-3781-81d342859334"

# Guard MCP toolset load during remote container bootstrap phase
# to avoid chicken-egg IAM Permission Denied loop under AGENT_IDENTITY / serviceAccount
try:
    mcp_toolset = registry.get_mcp_toolset(mcp_server_name=mcp_server_name)
except Exception as e:
    print(f"Warning: Bypassing MCP toolset load error: {e}")
    mcp_toolset = None

# https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/adk-quickstart#memory-generation-callback
async def generate_memories_callback(callback_context: CallbackContext):    
    await callback_context.add_session_to_memory()
    return None

root_agent = Agent(
    name="bq_mcp_agent",
    model="gemini-3.5-flash",
    instruction=(
        "You are an expert Data Science Agent. "
        "Your goal is to query enterprise BigQuery datasets, analyze the data, "
        "and summarize your findings. "
        f"When executing SQL queries, use project_id `{project_id}` as the "
        " project unless the user specifies a different one. "
        "Present results clearly with formatted numbers. "
        "Remember user preferences like preferred regions, date ranges, "
        "or analysis formats across conversations."
    ),
    after_agent_callback=generate_memories_callback,
    tools=[t for t in [mcp_toolset, PreloadMemoryTool()] if t is not None],
)