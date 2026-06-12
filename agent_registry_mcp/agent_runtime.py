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
print(f"Initializing Vertex AI Client (Project: {PROJECT_ID}, Location: {LOCATION})...")
client = vertexai.Client(
    project=PROJECT_ID,
    location=LOCATION,
    http_options=dict(api_version="v1beta1")
)

# Use the proper wrapper class for your Agent Framework
print("Wrapping agent in AdkApp...")
adk_app = AdkApp(agent=agent)

# # Create a new resource with your agent deployed to Agent Runtime.
# service_account_email = f"google-cloud-ops-agent-sa@{PROJECT_ID}.iam.gserviceaccount.com"

remote_agent = client.agent_engines.create(
    agent=adk_app,
    config={
        "display_name": "Agent Registry for MCP",        
        # "service_account": service_account_email,
        "identity_type": types.IdentityType.AGENT_IDENTITY,
        "requirements": [
            "google-adk[agent-identity,a2a]>=2.1.0",
            "a2a-sdk",
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
            "GOOGLE_CLOUD_LOCATION": "global",
            "IS_REMOTE_RUNTIME": "TRUE"
        }
    }
)

print("\n✅ Deployment successful!")
print(f"Remote Agent Name: {remote_agent.api_resource.name}")
effective_identity = remote_agent.api_resource.spec.effective_identity
print(f"Effective Identity: {effective_identity}")

print("\n[ 🔒 Required IAM Role Assignment Commands ]")
print("# Grant BigQuery query/view, Vertex AI call, and Storage permissions to the Agent Identity:")
for role in [
    "roles/bigquery.dataViewer",
    "roles/bigquery.jobUser",
    "roles/aiplatform.user",
    "roles/storage.objectAdmin",
]:
    print(f"gcloud projects add-iam-policy-binding {PROJECT_ID} \\")
    print(f"    --member=\"{effective_identity}\" \\")
    print(f"    --role=\"{role}\"")