#!/usr/bin/env python3
import os
import sys
import vertexai
import google.adk

# Ensure google-adk version is >= 2.2.0 to prevent deepcopy pickle lock errors
try:
    adk_ver = tuple(map(int, google.adk.__version__.split('.')[:3]))
except Exception:
    adk_ver = (0, 0, 0)

if adk_ver < (2, 2, 0):
    print(f"\n❌ ERROR: 구 버전 google-adk({google.adk.__version__})가 로드되었습니다.", file=sys.stderr)
    print("에이전트 배포 중 'cannot pickle _thread.lock' 오류가 발생하는 것을 방지하기 위해 google-adk>=2.2.0 버전이 반드시 필요합니다.", file=sys.stderr)
    print("해결을 위해 다음 명령어를 실행하여 가상환경을 업데이트하십시오:\n", file=sys.stderr)
    print("    uv sync\n", file=sys.stderr)
    print("또는:\n", file=sys.stderr)
    print("    pip install --upgrade \"google-adk>=2.2.0\"\n", file=sys.stderr)
    sys.exit(1)

from vertexai import types
from vertexai.agent_engines import AdkApp
# Prevent environment variables from overriding explicit SDK location parameters
os.environ.pop("GOOGLE_CLOUD_LOCATION", None)

# Configuration parameters
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "gcp-sandbox-kwlee")
LOCATION = os.environ.get("GCP_RESOURCES_LOCATION", "us-central1")
STAGING_BUCKET = os.environ.get("STAGING_BUCKET_URI", "gs://adk-sandbox-bucket")

# Initialize the Agent Platform client
print(f"Initializing Vertex AI Client (Project: {PROJECT_ID}, Location: {LOCATION})...")
client = vertexai.Client(
    project=PROJECT_ID,
    location=LOCATION
)

# Create top-level AgentEngine container and a managed sandbox under it
print("Creating top-level AgentEngine container...")
agent_engine = client.agent_engines.create()
container_name = agent_engine.api_resource.name
print(f"✅ AgentEngine container created: {container_name}")

print(f"Creating Agent Sandbox under {container_name}...")
operation = client.agent_engines.sandboxes.create(
    name=container_name,
    config=types.CreateAgentEngineSandboxConfig(display_name="Agent Sandbox"),
    spec={
        "code_execution_environment": {            
            "code_language": "LANGUAGE_PYTHON",  # Programming language for execution
            "machine_config": "MACHINE_CONFIG_VCPU4_RAM4GIB", # Resource settings
        }
    }
)
sandbox_name = operation.response.name
print(f"✅ Sandbox created successfully! Resource name: {sandbox_name}")

# Set the environment variable BEFORE importing the agent, so that
# the AgentEngineSandboxCodeExecutor is created with the explicit sandbox resource name.
print(f"Injecting SANDBOX_RESOURCE_NAME into local environment: {sandbox_name}")
os.environ["SANDBOX_RESOURCE_NAME"] = sandbox_name

# Now import the agent cleanly
from agent import root_agent as agent

# Use the proper wrapper class for your Agent Framework
print("Wrapping agent in AdkApp...")
adk_app = AdkApp(agent=agent)

# Deploy Agent to Vertex AI Agent Runtime by updating the same container
print("Deploying Agent to Agent Runtime container...")
remote_agent = client.agent_engines.update(
    name=container_name,
    agent=adk_app,
    config={
        "display_name": "Agent Sandbox",
        "requirements": [
            "google-adk==2.2.0",
            "google-cloud-aiplatform[adk,agent_engines]==1.157.0",
            "pydantic==2.13.4",
            "cloudpickle==3.1.2"
        ],
        "staging_bucket": STAGING_BUCKET,
        "extra_packages": [os.path.join(os.path.dirname(__file__), "agent.py")],
        "env_vars": {
            "GOOGLE_CLOUD_LOCATION": "global",
            "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
            # SessionService, MemoryService, ArtifactService
            "ADK_SESSION_SERVICE_URI": "agentengine://",
            "ADK_MEMORY_SERVICE_URI": "agentengine://",
            "ADK_ARTIFACT_SERVICE_URI": STAGING_BUCKET,
            # Telemetry            
            "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
            "OTEL_SEMCONV_STABILITY_OPT_IN": "gen_ai_latest_experimental",
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "EVENT_ONLY",
            # Sandbox configuration injection
            "SANDBOX_RESOURCE_NAME": sandbox_name
        }
    },
)

print("\n✅ Deployment successful!")
print(f"Remote Agent Name: {remote_agent.api_resource.name}")