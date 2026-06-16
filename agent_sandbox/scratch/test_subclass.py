import os
import threading
import cloudpickle
from google.adk.code_executors.agent_engine_sandbox_code_executor import AgentEngineSandboxCodeExecutor

class PatchedAgentEngineSandboxCodeExecutor(AgentEngineSandboxCodeExecutor):
    @property
    def _agent_engine_creation_lock(self):
        print("Getter called!")
        if hasattr(self, "__pydantic_private__") and self.__pydantic_private__ is not None:
            if "_agent_engine_creation_lock" not in self.__pydantic_private__:
                self.__pydantic_private__["_agent_engine_creation_lock"] = threading.Lock()
            return self.__pydantic_private__["_agent_engine_creation_lock"]
        if "_agent_engine_creation_lock" not in self.__dict__:
            self.__dict__["_agent_engine_creation_lock"] = threading.Lock()
        return self.__dict__["_agent_engine_creation_lock"]

# Test instantiation
executor = PatchedAgentEngineSandboxCodeExecutor(
    sandbox_resource_name="projects/test/locations/us-central1/reasoningEngines/123/sandboxEnvironments/456"
)

# Test lock access
print("Accessing lock...")
lock = executor._agent_engine_creation_lock
print("Lock:", lock)

# Test pickle/unpickle
print("\nPickling...")
pickled = cloudpickle.dumps(executor)
print("Unpickling...")
unpickled = cloudpickle.loads(pickled)

print("\nAccessing lock on unpickled executor...")
lock_unpickled = unpickled._agent_engine_creation_lock
print("Lock on unpickled:", lock_unpickled)
