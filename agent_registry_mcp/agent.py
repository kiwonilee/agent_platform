import os

from google.adk.integrations.agent_registry import AgentRegistry
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.tools.base_toolset import BaseToolset

from google.auth import default
from google.genai import types
from google.adk.apps import App

project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "gcp-sandbox-kwlee")
location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")

# Initialize the client
registry = AgentRegistry(
    project_id=project_id,
    location=location,
)

class LazyMCPToolset(BaseToolset):
    """MCP Toolset wrapper that defers tool registration API requests until runtime."""
    def __init__(self, registry, server_resource_name, **kwargs):
        super().__init__(**kwargs)
        self._registry = registry
        self._server_resource_name = server_resource_name
        self._toolset = None

    def _get_toolset(self):
        if self._toolset is None:
            self._toolset = self._registry.get_mcp_toolset(self._server_resource_name)
        return self._toolset

    async def get_tools(self, readonly_context=None):
        return await self._get_toolset().get_tools(readonly_context)

# Retrieve an MCP toolset lazily using its resource name in short or full format
mcp_toolset = LazyMCPToolset(
    registry,
    f"projects/gcp-sandbox-kwlee/locations/global/mcpServers/agentregistry-00000000-0000-0000-3781-81d342859334"
)

# https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/adk-quickstart#memory-generation-callback
async def generate_memories_callback(callback_context: CallbackContext):    
    await callback_context.add_session_to_memory()
    return None

root_agent = Agent(
    name="bq_mcp_agent",
    model=Gemini(
            model="gemini-flash-latest",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
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
    tools=[mcp_toolset, PreloadMemoryTool()],
    after_agent_callback=generate_memories_callback,
)

app = App(
    name="bq_mcp_agent",
    root_agent=root_agent,
)