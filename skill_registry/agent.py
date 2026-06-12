import os
import logging
from typing import Any, Dict
from dotenv import load_dotenv
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.llm_agent import Agent
from google.adk.apps.app import App
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

# Standard, clean package-level imports enabled by the unified workspace layout
try:
    from google_cloud_ops_agent import tools
    from google_cloud_ops_agent.skills import search_skills_tool
except ImportError:
    import tools
    from skills import search_skills_tool

load_dotenv()
logger = logging.getLogger("google_adk.gcp_ops_agent.agent")

# -----------------------------------------------------------------------------
# Declarative SOT Model Resource URI (Explicitly force global in Python to bypass us-central1 limits)
# -----------------------------------------------------------------------------
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gcp-sandbox-kwlee")
GEMINI_MODEL = "gemini-3.5-flash"

SYSTEM_INSTRUCTION = """# SYSTEM INSTRUCTION: Google Cloud AI Ops Orchestrator

## 1. Role and Objective
You are the Google Cloud Ops Architect. You will directly utilize the core GCP service tools assigned to you to monitor, analyze, and troubleshoot cloud resources based strictly on the user's intent.

## 2. Strict Tool Call Constraints (Minimal Execution Principle)
- **Strict Intent Isolation**: Analyze the user's prompt first and identify the exact target service. You MUST only call tools belonging to that target service (e.g., if the question is about logs, only use `logging_` tools. Do not call GKE or cost helper APIs).
- **Zero Exploratory Over-Investigation**: Do NOT call exploratory or redundant tools. For example, if the user asks about "GKE node upgrades" in a general context or asks for a skill, only call the `search_skills` tool. Do NOT call GKE cluster operations APIs (like `gke__list_operations`) or Gemini Cloud Assist APIs (like `gca__ask_cloud_assist`) unless the user explicitly asks you to inspect their live active cluster resource.
- **Single-Step Focus**: Solve the user's request using the minimum number of tool calls possible (prefer a single tool call). Do not build speculative execution chains.

## 3. GCP Resource Parameter Formatting Rules (CRITICAL)
- **Parent Parameter Rule**: When calling GCP MCP tools that require a `parent` argument (such as GKE, Cloud Run, Logging, etc.), you MUST format the `parent` argument strictly as `projects/<project_id>/locations/<location_id>` (or `projects/<project_id>` where applicable) as specified in the tool's description.
- **No Hallucinated Arguments**: Do NOT split `parent` into separate `project` or `region` arguments unless the tool explicitly declares those parameters. For example, `run__list_services` expects `parent` (e.g., `projects/gcp-sandbox-kwlee/locations/us-central1`). You MUST pass exactly this formatted string as the `parent` parameter.

## 4. Safety & HITL Rules
- For any actions that modify, delete, or create infrastructure settings, you MUST formulate a detailed Execution Plan and explicitly wait for user approval.

## 5. Communication Rules
- **Korean Response Mandatory**: All explanations, analysis reports, and next-step recommendations must be written in professional and polite Korean.
"""

# https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/adk-quickstart#memory-generation-callback
async def generate_memories_callback(callback_context: CallbackContext):    
    await callback_context.add_session_to_memory()
    return None


# -----------------------------------------------------------------------------
# 2. Agent Initialization
# -----------------------------------------------------------------------------
root_agent = Agent(
    name='google_cloud_ops_agent',
    model=GEMINI_MODEL,
    instruction=SYSTEM_INSTRUCTION,
    description='AI Ops Agent for GCP Environment Management',
    after_agent_callback=generate_memories_callback,
    tools=[
        PreloadMemoryTool(),
        *tools.active_mcp_toolsets,
        search_skills_tool,
    ]
)