import os
import sys
import vertexai
from vertexai import types
from vertexai.agent_engines import AdkApp
from agent import root_agent as agent

# Configuration parameters
PROJECT_ID = "gcp-sandbox-kwlee"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://adk-sandbox-bucket"

# Initialize the Agent Platform client with v1beta1 API for agent identity support
# https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/agent-identity#create-agent-identity
client = vertexai.Client(
    project=PROJECT_ID,
    location=LOCATION,
    http_options=dict(api_version="v1beta1")
)

# Use the proper wrapper class for your Agent Framework
print("Wrapping agent in AdkApp...")
adk_app = AdkApp(agent=agent)

# Create a new resource with your agent deployed to Agent Runtime.
service_account_email = f"google-cloud-ops-agent-sa@{PROJECT_ID}.iam.gserviceaccount.com"

remote_agent = client.agent_engines.create(
    agent=adk_app,
    config={
        "display_name": "Agent Registry for MCP",        
        "service_account": service_account_email,
        "requirements": [
            "google-adk[agent-identity,a2a]>=2.1.0",
            "google-cloud-aiplatform[agent_engines]",
            "cloudpickle",
            "pydantic",
            "mcp",
        ],        
        "staging_bucket": STAGING_BUCKET,
        "extra_packages": ["agent.py"],
        "env_vars": {
            "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
            # SessionService, MemoryService, ArtifactService
            "ADK_SESSION_SERVICE_URI": "agentengine://",
            "ADK_MEMORY_SERVICE_URI": "agentengine://",
            "ADK_ARTIFACT_SERVICE_URI": STAGING_BUCKET,
            # Telemetry            
            "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
            "OTEL_SEMCONV_STABILITY_OPT_IN": "gen_ai_latest_experimental",
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "EVENT_ONLY",
            # Context-Aware Access 해제 ( Agent Identity 했을 때, 401 UNAUTHENTICATED 오류 나는 경우)
            # https://docs.cloud.google.com/iam/docs/auth-agent-own-identity?hl=ko#opt-out-caa
            # https://docs.cloud.google.com/iam/docs/troubleshoot-auth-manager?hl=ko#401-error
            "GOOGLE_API_PREVENT_AGENT_TOKEN_SHARING_FOR_GCP_SERVICES": "False",
            # Force global location for AgentRegistry lookup, otherwise container default us-central1 overrides it
            "GOOGLE_CLOUD_LOCATION": "global"
        }
    }
)

print("\n✅ Deployment successful!")
print(f"Remote Agent Name: {remote_agent.api_resource.name}")
print(f"Effective Identity: {remote_agent.api_resource.spec.effective_identity}")