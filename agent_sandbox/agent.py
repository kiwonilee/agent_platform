# https://adk.dev/integrations/code-exec-agent-runtime/
# 
# The two code execution options are:
# 1. AgentEngineSandboxCodeExecutor - Uses Vertex AI's managed sandbox (what we've been using)
# 2. BuiltInCodeExecutor - ADK's native code execution (simpler, integrated)

import os
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.code_executors.agent_engine_sandbox_code_executor import AgentEngineSandboxCodeExecutor

# Monkey-patch AgentEngineSandboxCodeExecutor to handle uncopyable/unpicklable fields (like thread locks and client services)
import copy
import threading

def _code_executor_deepcopy(self, memo):
    cls = self.__class__
    result = cls.__new__(cls)
    memo[id(self)] = result
    
    # Deepcopy the __dict__ but exclude/modify any uncopiable attributes
    new_dict = {}
    for k, v in self.__dict__.items():
        if k in ('_sandbox_service', '_client', 'client') or type(v).__name__ == 'lock':
            new_dict[k] = None
        else:
            new_dict[k] = copy.deepcopy(v, memo)
            
    object.__setattr__(result, '__dict__', new_dict)
    
    for attr in ('__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'):
        if hasattr(self, attr):
            val = getattr(self, attr)
            if attr == '__pydantic_fields_set__':
                copied_val = copy.copy(val)
            elif attr == '__pydantic_private__':
                if val is None:
                    copied_val = None
                else:
                    copied_val = {}
                    for pk, pv in val.items():
                        if pk in ('_sandbox_service', '_client', 'client') or type(pv).__name__ == 'lock' or pk == '_agent_engine_creation_lock':
                            copied_val[pk] = threading.Lock()
                        else:
                            copied_val[pk] = copy.deepcopy(pv, memo)
            else:
                copied_val = copy.deepcopy(val, memo)
            object.__setattr__(result, attr, copied_val)
            
    return result

def _code_executor_getstate(self):
    state = self.__dict__.copy()
    for k in list(state.keys()):
        if k in ('_sandbox_service', '_client', 'client') or type(state[k]).__name__ == 'lock':
            state[k] = None
            
    if hasattr(self, '__pydantic_private__') and self.__pydantic_private__:
        private_state = self.__pydantic_private__.copy()
        for pk in list(private_state.keys()):
            if pk in ('_sandbox_service', '_client', 'client') or type(private_state[pk]).__name__ == 'lock' or pk == '_agent_engine_creation_lock':
                private_state[pk] = None
        state['__pydantic_private__'] = private_state
        
    return state

def _code_executor_setstate(self, state):
    private_state = state.pop('__pydantic_private__', None)
    if private_state:
        private_state['_agent_engine_creation_lock'] = threading.Lock()
        object.__setattr__(self, '__pydantic_private__', private_state)
        
    for k, v in state.items():
        object.__setattr__(self, k, v)

AgentEngineSandboxCodeExecutor.__deepcopy__ = _code_executor_deepcopy
AgentEngineSandboxCodeExecutor.__getstate__ = _code_executor_getstate
AgentEngineSandboxCodeExecutor.__setstate__ = _code_executor_setstate

load_dotenv()

# Read the sandbox resource name from environment variable, default to a placeholder
sandbox_resource_name = os.getenv(
    "SANDBOX_RESOURCE_NAME",
    "projects/YOUR_PROJECT_ID/locations/us-central1/customSandboxes/YOUR_SANDBOX_ID"
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
    code_executor=AgentEngineSandboxCodeExecutor(
        sandbox_resource_name=sandbox_resource_name
    ),
    output_key="analysis_result",  # Store result in session state
)


