import os
import sys
from dotenv import load_dotenv
from vertexai.agent_engines import AdkApp

project_parent = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
os.chdir(project_parent)
if project_parent not in sys.path:
    sys.path.insert(0, project_parent)

# Load configurations dynamically from .env
load_dotenv(os.path.join(project_parent, "google_cloud_ops_agent/.env"))

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gcp-sandbox-kwlee")
LOCATION = os.getenv("GCP_RESOURCES_LOCATION", "us-central1")  # Agent Engine is deployed regionally

# CLIENT & AGENT PLATFORM INITIALIZATION
import vertexai

client = vertexai.Client(
    project=PROJECT_ID, 
    location=LOCATION
)

# Import the SRE root agent using the fully qualified package namespace
from google_cloud_ops_agent.agent import app
adk_app = AdkApp(app=app)

# -----------------------------------------------------------------------------
# Environment variables dynamically loaded from .env
# -----------------------------------------------------------------------------
sre_env_keys = [
    "GOOGLE_GENAI_USE_VERTEXAI",
    "GCP_RESOURCES_LOCATION",
    "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY",
    "OTEL_SEMCONV_STABILITY_OPT_IN",
    "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT",
]
env_vars = {key: os.environ[key] for key in sre_env_keys if key in os.environ}

# -----------------------------------------------------------------------------
# Explicitly append Production Runtime URIs to the env_vars payload dictionary
# -----------------------------------------------------------------------------
env_vars["GOOGLE_CLOUD_LOCATION"] = "global"

env_vars["ADK_DISABLE_JSON_SCHEMA_FOR_FUNC_DECL"] = "1"
env_vars["ADK_ENABLE_FEATURES"] = "SKILL_TOOLSET"

env_vars["ADK_SESSION_SERVICE_URI"] = "agentengine://"
env_vars["ADK_MEMORY_SERVICE_URI"] = "agentengine://"
env_vars["ADK_ARTIFACT_SERVICE_URI"] = "gs://adk-sandbox-bucket"

requirements_list = [
    "google-genai",
    "google-auth",
    "google-adk",
    "google-cloud-aiplatform[agent_engines]",
    "python-dotenv",
    "pydantic",
    "cloudpickle",
    "mcp>=1.27.1",
    "pyyaml>=6.0.3",
]

# Construct the custom service account email and staging bucket dynamically
service_account_email = f"google-cloud-ops-agent-sa@{PROJECT_ID}.iam.gserviceaccount.com"
staging_bucket_uri = os.environ.get("ADK_ARTIFACT_SERVICE_URI", f"gs://adk-sandbox-bucket")

print(f"Deploying 'google_cloud_ops_agent' to AgentPlatform...")

# Create a new resource with your agent deployed to Agent Runtime.
remote_agent = client.agent_engines.create(
    agent=adk_app,
    config={
        "display_name": "Google Cloud Ops Agent",
        "description": "Managed AI Ops Architect for GCP SRE Operations",
        "requirements": requirements_list,
        "extra_packages": ["google_cloud_ops_agent"],
        "env_vars": env_vars,
        "service_account": service_account_email,
        "staging_bucket": staging_bucket_uri,
    }
)

print(f"\nSUCCESS: Agent deployed successfully to Agent Runtime!")
print(f"AgentPlatform Resource Name: {remote_agent.api_resource.name}")
print(f"To run chat sessions on this deployed agent, use the resource URI: {remote_agent.api_resource.name}")