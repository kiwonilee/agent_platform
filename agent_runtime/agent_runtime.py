import os
import sys
import vertexai
from vertexai import types
from vertexai.agent_engines import AdkApp
from agent import root_agent as agent

# Configuration parameters
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "gcp-sandbox-kwlee")
LOCATION = os.environ.get("GCP_RESOURCES_LOCATION", "us-central1")
STAGING_BUCKET = os.environ.get("STAGING_BUCKET_URI", "gs://adk-sandbox-bucket")

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
print("Deploying Agent to Agent Runtime...")
remote_agent = client.agent_engines.create(
    agent=adk_app,
    # https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/deploy-an-agent#install_gcloud_cli.sh
    config={
        "display_name": "Agent Registry for MCP",        
        # "service_account": service_account_email,
        "identity_type": types.IdentityType.AGENT_IDENTITY,
        "min_instances": 1,
        "max_instances": 10,
        "resource_limits": {"cpu": "1", "memory": "1Gi"},
        # recommend : 2 * cpu+ 1
        "container_concurrency": 9,
        "requirements": [
            # See https://pypi.org/project/google-cloud-aiplatform for the latest version.
            "google-cloud-aiplatform[agent_engines,adk]",
            "pydantic",
            "cloudpickle==3.0", # new
        ],  
        "extra_packages": ["agent.py"],
        "env_vars": {
            "GOOGLE_CLOUD_LOCATION": "global",
            "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
            # Telemetry            
            "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
            "OTEL_SEMCONV_STABILITY_OPT_IN": "gen_ai_latest_experimental",
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "EVENT_ONLY",
            # Context-Aware Access 해제 ( Agent Identity 했을 때, 401 UNAUTHENTICATED 오류 나는 경우)
            # https://docs.cloud.google.com/iam/docs/auth-agent-own-identity?hl=ko#opt-out-caa
            # https://docs.cloud.google.com/iam/docs/troubleshoot-auth-manager?hl=ko#401-error
            "GOOGLE_API_PREVENT_AGENT_TOKEN_SHARING_FOR_GCP_SERVICES": "False"
        },
        "gcs_dir_name": "None",
        "agent_fremework": "google-adk"
    }
)

print("\n✅ Deployment successful!")
print(f"Remote Agent Name: {remote_agent.api_resource.name}")
effective_identity = remote_agent.api_resource.spec.effective_identity
print(f"Agent Identity: {effective_identity}")