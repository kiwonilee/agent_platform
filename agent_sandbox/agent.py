# https://adk.dev/integrations/code-exec-agent-runtime/
# 
# Using AgentEngineSandboxCodeExecutor to run Python code safely inside
# Vertex AI's managed sandbox environment.

import os
from google.adk.agents.llm_agent import Agent
from google.adk.code_executors.agent_engine_sandbox_code_executor import AgentEngineSandboxCodeExecutor

# Explicitly use AgentEngineSandboxCodeExecutor
sandbox_resource_name = os.getenv("SANDBOX_RESOURCE_NAME")

if sandbox_resource_name:
    code_executor = AgentEngineSandboxCodeExecutor(
        sandbox_resource_name=sandbox_resource_name
    )
else:
    # If not set, let the SDK lazily create or manage sandbox environments using ambient project/location settings.
    code_executor = AgentEngineSandboxCodeExecutor()


root_agent = Agent(
    model="gemini-3.5-flash",
    name="agent_sandbox",
    instruction="""You are a helpful coding assistant. When asked to perform calculations or data processing:

    1. Write clear, well-commented Python code inside a markdown code block (starting with ```python and ending with ```)
    2. Include print statements to show intermediate steps
    3. Use the code execution tool to run your code
    4. Explain the results in a user-friendly way

    Always ensure your code is complete and executable.
    """,
    code_executor=code_executor,
    output_key="analysis_result",  # Store result in session state
)