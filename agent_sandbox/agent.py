# https://adk.dev/integrations/code-exec-agent-runtime/
# 
# The two code execution options are:
# 1. AgentEngineSandboxCodeExecutor - Uses Vertex AI's managed sandbox (what we've been using)
# 2. BuiltInCodeExecutor - ADK's native code execution (simpler, integrated)

import os
from google.adk.agents.llm_agent import Agent
from google.adk.code_executors.built_in_code_executor import BuiltInCodeExecutor

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
    code_executor=BuiltInCodeExecutor(),
    output_key="analysis_result",  # Store result in session state
)



