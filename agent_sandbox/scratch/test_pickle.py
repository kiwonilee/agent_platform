import os
import cloudpickle
from google.adk.code_executors.agent_engine_sandbox_code_executor import AgentEngineSandboxCodeExecutor

# Initialize executor
executor = AgentEngineSandboxCodeExecutor(sandbox_resource_name="projects/test-project/locations/us-central1/reasoningEngines/123/sandboxEnvironments/456")
print("Original executor lock:", getattr(executor, "_agent_engine_creation_lock", None))

# Serialize and deserialize
pickled = cloudpickle.dumps(executor)
unpickled = cloudpickle.loads(pickled)

print("Unpickled executor lock:", getattr(unpickled, "_agent_engine_creation_lock", None))
try:
    lock = unpickled._agent_engine_creation_lock
    print("Direct access to lock:", lock)
except Exception as e:
    print("Error accessing lock:", type(e), e)
