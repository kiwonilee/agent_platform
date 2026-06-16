import os
import sys
import vertexai
from vertexai.agent_engines import AdkApp
from agent import root_agent as agent

# Configuration parameters
PROJECT_ID = "gcp-sandbox-kwlee"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://adk-sandbox-bucket"

# CLIENT & AGENT PLATFORM INITIALIZATION
print(f"Initializing Vertex AI Client (Project: {PROJECT_ID}, Location: {LOCATION})...")
client = vertexai.Client(
    project=PROJECT_ID, 
    location=LOCATION
)

# Use the proper wrapper class for your Agent Framework
print("Wrapping agent in AdkApp...")
adk_app = AdkApp(agent=agent)

# Create a new resource with your agent deployed to Agent Runtime.
remote_agent = client.agent_engines.create(
    agent=adk_app,
    config={
        "display_name": "Agent Skills",
        "identity_type": types.IdentityType.AGENT_IDENTITY,
        "requirements": [
            "google-genai",
            "google-auth",
            "google-adk[agent-identity,a2a]>=2.1.0",
            "google-cloud-aiplatform[agent_engines]",
            "python-dotenv",
            "pydantic",
            "cloudpickle",
            "mcp>=1.27.1",
            "pyyaml>=6.0.3",
        ],
        "staging_bucket": STAGING_BUCKET,
        "extra_packages": ["agent.py"],
        "env_vars": {
            "GOOGLE_CLOUD_LOCATION": "global",
            "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
            # Telemetry            
            "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
            "OTEL_SEMCONV_STABILITY_OPT_IN": "gen_ai_latest_experimental",
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "EVENT_ONLY",
        }
    }
)

print("\n✅ Deployment successful!")
print(f"Remote Agent Name: {remote_agent.api_resource.name}")
effective_identity = remote_agent.api_resource.spec.effective_identity
print(f"Agent Identity: {effective_identity}")

print("\n[ 🔒 Required IAM Role Assignment Commands ]")
print("# Grant as following permissions to the Agent Identity:")
for role in [
    "roles/aiplatform.viewer",
    "roles/aiplatform.user",
    "roles/serviceusage.serviceUsageConsumer"
]:
    print(f"gcloud projects add-iam-policy-binding {PROJECT_ID} \\")
    print(f"    --member=\"principal://{effective_identity}\" \\")
    print(f"    --role=\"{role}\"")