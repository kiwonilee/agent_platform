import os
import sys
from dotenv import load_dotenv
from vertexai.agent_engines import AdkApp

# Set up project path namespaces and change directory to parent to allow proper bq_mcp_agent packaging
project_parent = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(project_parent)
if project_parent not in sys.path:
    sys.path.insert(0, project_parent)

# Load configurations from the project's .env file
load_dotenv(os.path.join(project_parent, "agent_registry_mcp/.env"))

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gcp-sandbox-kwlee")
LOCATION = os.getenv("GCP_RESOURCES_LOCATION", "us-central1")

# Initialize client with v1beta1 support for Agent Identity
import vertexai
from vertexai import types as vertexai_types

client = vertexai.Client(
    project=PROJECT_ID,
    location=LOCATION,
    #  "identity_type": vertexai_types.IdentityType.AGENT_IDENTITY, 를 위해 필요
    http_options=dict(api_version="v1beta1")
)

# Import and wrap the Data Science app via its package path
from agent_registry_mcp.agent import root_agent as agent
adk_app = AdkApp(agent=agent)

# -----------------------------------------------------------------------------
# Environment variables dynamically loaded from .env
# -----------------------------------------------------------------------------
bq_env_keys = [
    "GOOGLE_GENAI_USE_VERTEXAI",
    "GCP_RESOURCES_LOCATION",
    "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY",
    "OTEL_SEMCONV_STABILITY_OPT_IN",
    "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT",
]
env_vars = {key: os.environ[key] for key in bq_env_keys if key in os.environ}

# -----------------------------------------------------------------------------
# Explicitly append Production Runtime URIs to the env_vars payload dictionary
# -----------------------------------------------------------------------------
env_vars["GOOGLE_CLOUD_LOCATION"] = "global"

env_vars["ADK_SESSION_SERVICE_URI"] = "agentengine://"
env_vars["ADK_MEMORY_SERVICE_URI"] = "agentengine://"
env_vars["ADK_ARTIFACT_SERVICE_URI"] = "gs://adk-sandbox-bucket"

requirements_list = [
    "google-genai",
    "google-auth>=2.53.0",
    "google-adk[agent-identity]>=2.1.0",
    "a2a-sdk>=0.3.4,<0.4",
    "mcp>=1.27.1",
    "google-cloud-aiplatform[agent_engines]>=1.154.0",
    "python-dotenv",
    "pydantic",
    "cloudpickle",
    "pyyaml",
    "google-api-core",
]

# service_account_email = f"google-cloud-ops-agent-sa@{PROJECT_ID}.iam.gserviceaccount.com"
staging_bucket_uri = os.environ.get("ADK_ARTIFACT_SERVICE_URI", "gs://adk-sandbox-bucket")

print(f"Deploying 'agent_registry_mcp' to AgentPlatform in a single step...")

# Create a new resource with your agent deployed to Agent Runtime.
remote_agent = client.agent_engines.create(
    agent=adk_app,
    config={
        "display_name": "BigQuery MCP Agent",
        "description": "Expert Data Science Agent for querying enterprise BigQuery datasets, analyzing data, and summarizing findings.",
        "requirements": requirements_list,
        "extra_packages": ["agent_registry_mcp"],
        "env_vars": env_vars,
        "identity_type": vertexai_types.IdentityType.AGENT_IDENTITY,
        # "service_account": service_account_email,
        "staging_bucket": staging_bucket_uri,
    }
)

print(f"\nSUCCESS: Agent deployed successfully to Agent Runtime!")
print(f"AgentPlatform Resource Name: {remote_agent.api_resource.name}")
print(f"To run chat sessions on this deployed agent, use the resource URI: {remote_agent.api_resource.name}")
