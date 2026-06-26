import os
import sys
from dotenv import load_dotenv
import vertexai

from vertexai import types
from vertexai.agent_engines import AdkApp
from agent import root_agent as agent

# Load environment variables from .env
load_dotenv()

# Configuration parameters
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GCP_RESOURCES_LOCATION", "us-central1")
STAGING_BUCKET = os.environ.get("STAGING_BUCKET_URI")
SERVICE_ACCOUNT = os.environ.get("SERVICE_ACCOUNT")

print(f"Initializing Vertex AI Client (Project: {PROJECT_ID}, Location: {LOCATION})...")
client = vertexai.Client(
    project=PROJECT_ID,
    location=LOCATION
)

# Use the proper wrapper class for your Agent Framework
print("Wrapping agent in AdkApp...")
adk_app = AdkApp(agent=agent)

# Load optional custom service account from .env
service_account_email = os.environ.get("DEPLOY_SERVICE_ACCOUNT")

# Create a new resource with your agent deployed to Agent Runtime.
print("Deploying Agent to Agent Runtime...")
deploy_config = {
    "display_name": "Agent Registry",
    "requirements": [
        "google-adk[agent-identity,a2a]>=2.2.0",
        "a2a-sdk>=0.3.4,<0.4",
        "google-cloud-aiplatform[adk,agent_engines]>=1.157.0",
        "cloudpickle",
        "pydantic",
        "mcp>=1.27.1",
    ],
    "staging_bucket": STAGING_BUCKET,
    "extra_packages": ["agent.py"],
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
        "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "EVENT_ONLY"
    }
}

# Robust resolution of the service account email (prevents duplicate suffixing)
final_sa = service_account_email or SERVICE_ACCOUNT

if final_sa:
    if "@" in final_sa:
        deploy_config["service_account"] = final_sa
    else:
        deploy_config["service_account"] = f"{final_sa}@{PROJECT_ID}.iam.gserviceaccount.com"


remote_agent = client.agent_engines.create(
    agent=adk_app,
    config=deploy_config
)


print("\n✅ Deployment successful!")
print(f"Remote Agent Name: {remote_agent.api_resource.name}")
effective_identity = remote_agent.api_resource.spec.effective_identity
print(f"Agent Identity: {effective_identity}")