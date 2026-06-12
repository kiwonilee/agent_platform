import os
from google.adk.integrations.agent_registry import AgentRegistry

project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "gcp-sandbox-kwlee")
location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")

# Initialize the registry client
registry = AgentRegistry(
    project_id=project_id,
    location=location,
)

# Active SRE MCP Servers harvested from task-197.log
mcp_servers = [
    "mcpServers/agentregistry-00000000-0000-0000-861b-11c2ceb07996",  # GKE
    "mcpServers/agentregistry-00000000-0000-0000-0c34-a2d85a151b0f",  # Run
    "mcpServers/agentregistry-00000000-0000-0000-33ac-b82d3e783371",  # Logging
    "mcpServers/agentregistry-00000000-0000-0000-2804-6e4bcd24a2b3",  # Monitoring
    "mcpServers/agentregistry-00000000-0000-0000-b007-f227b81a79b9",  # Gemini Assist
    "mcpServers/agentregistry-00000000-0000-0000-2c61-77e00c7e4574",  # SQL Admin
    "mcpServers/agentregistry-00000000-0000-0000-2039-99a6285dcb61",  # Storage / BigQuery
]

active_mcp_toolsets = [registry.get_mcp_toolset(mcp_server_name=s) for s in mcp_servers]
