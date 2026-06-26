import os
import httpx
import google.auth

from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.adk.integrations.agent_registry import AgentRegistry
from google.adk.agents.llm_agent import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

from google.genai import types
from google.adk.apps import App

# Load environment variables from .env
load_dotenv()

# Initialize the registry client
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")

# Initialize the client
registry = AgentRegistry(
    project_id=project_id,
    location=location,
)

# Retrieve an MCP toolset using its resource name in short or full format
mcp_server_name = os.environ.get("MCP_SERVER_NAME")
mcp_toolset = registry.get_mcp_toolset(mcp_server_name=mcp_server_name)

# https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/adk-quickstart#memory-generation-callback
async def generate_memories_callback(callback_context: CallbackContext):    
    await callback_context.add_session_to_memory()
    return None

root_agent = Agent(
    name="agent_registry_agent",
    model="gemini-3.5-flash",
    instruction=(
        "You are an AI logging agent who can answer questions.\n"
        "Your target Google Cloud Project ID is '{project_id?}'.\n"
        "If the target project_id is empty, None, or not set, politely ask the user to provide their Google Cloud Project ID first. "        
    ),
    after_agent_callback=generate_memories_callback,
    tools=[mcp_toolset, PreloadMemoryTool()]
)