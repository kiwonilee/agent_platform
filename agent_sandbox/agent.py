# https://adk.dev/integrations/code-exec-agent-runtime/
# 
# Using AgentEngineSandboxCodeExecutor to run Python code safely inside
# Vertex AI's managed sandbox environment.

import os
from google.adk.agents.llm_agent import Agent
from google.adk.code_executors.agent_engine_sandbox_code_executor import AgentEngineSandboxCodeExecutor

# Explicitly use AgentEngineSandboxCodeExecutor
sandbox_resource_name = os.getenv(
    "SANDBOX_RESOURCE_NAME",
    "projects/123456789012/locations/us-central1/sandboxes/123456789012"
)
code_executor = AgentEngineSandboxCodeExecutor(
    sandbox_resource_name=sandbox_resource_name
)

data_analyst = Agent(
    model="gemini-3.5-flash",
    name="data_analyst",
    description="Expert data analyst for sales and business metrics",
    instruction="""You are a helpful coding assistant. When asked to perform calculations or data processing:

    1. Write clear, well-commented Python code
    2. Include print statements to show intermediate steps
    3. Use the code execution tool to run your code
    4. Explain the results in a user-friendly way

    Always ensure your code is complete and executable.
    """,
    code_executor=code_executor,
    output_key="analysis_result",  # Store result in session state
)





