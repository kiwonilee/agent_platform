import os
import sys
import vertexai

from dotenv import load_dotenv
from vertexai import types
from vertexai.agent_engines import AdkApp
from agent import root_agent as agent

# Load environment variables from .env
load_dotenv(override=True)

# Configuration parameters
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GCP_RESOURCES_LOCATION", "us-central1")
STAGING_BUCKET = os.environ.get("STAGING_BUCKET_URI")
SERVICE_ACCOUNT = os.environ.get("SERVICE_ACCOUNT")

print(f"Initializing Vertex AI Client (Project: {PROJECT_ID}, Location: {LOCATION}, Service Account: {SERVICE_ACCOUNT})...")
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
        "service_account" : SERVICE_ACCOUNT,
        "requirements": [
            "google-adk[agent-identity,a2a]>=2.2.0",
            "google-cloud-aiplatform[agent_engines]",
            "google-genai",
            "google-auth",
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
            # SessionService, MemoryService, ArtifactService
            "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
            "OTEL_SEMCONV_STABILITY_OPT_IN": "gen_ai_latest_experimental",
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "EVENT_ONLY",
            # Telemetry
            "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
            "OTEL_SEMCONV_STABILITY_OPT_IN": "gen_ai_latest_experimental",
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "EVENT_ONLY"
        }
    }
)

print("\n✅ Deployment successful!")
print(f"Remote Agent Name: {remote_agent.api_resource.name}")
effective_identity = remote_agent.api_resource.spec.effective_identity
print(f"Agent Identity: {effective_identity}")