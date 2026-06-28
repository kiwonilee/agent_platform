import os
import sys
import vertexai

from dotenv import load_dotenv
load_dotenv(override=True)

from vertexai import types
from vertexai.agent_engines import AdkApp
from agent import root_agent as agent

# Configuration parameters
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GCP_RESOURCES_LOCATION")
STAGING_BUCKET = os.environ.get("STAGING_BUCKET_URI")

# Initialize the Agent Platform client with v1beta1 API for agent identity support
# https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/agent-identity#create-agent-identity
print(f"Initializing Vertex AI Client (Project: {PROJECT_ID}, Location: {LOCATION}...")
client = vertexai.Client(
    project=PROJECT_ID,
    location=LOCATION,
    http_options=dict(api_version="v1beta1")
)

# Use the proper wrapper class for your Agent Framework
print("Wrapping agent in AdkApp...")
adk_app = AdkApp(agent=agent)

# https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/setup?hl=ko#memory-bank-config
memory_bank_config = {
    # Default TTL for memory revisions is 365 days.
    "ttl_config": {"default_ttl": f"{365 * 24 * 60 * 60}s"},
    # Default Model for Memory Bank is gemini-2.5-flash
    "generation_config": {
        "model": f"projects/{PROJECT_ID}/locations/global/publishers/google/models/gemini-3.5-flash",
    },
    # Default for Similarity Search Model is text-embedding-005
    # text-embedding-005 is supported only English, but gemini-embedding-2 is supported multilingual.
    "similarity_search_config": {
        "embedding_model": f"projects/{PROJECT_ID}/locations/global/publishers/google/models/gemini-embedding-2"
    },
    "customization_configs": [
        {"consolidation_config": {"revisions_per_candidate_count": 3}}
    ],
}

# # Create a new resource with your agent deployed to Agent Runtime.
# service_account_email = f"google-cloud-ops-agent-sa@{PROJECT_ID}.iam.gserviceaccount.com"
print("Deploying Agent to Agent Runtime...")
remote_agent = client.agent_engines.create(
    agent=adk_app,
    # https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/deploy-an-agent#install_gcloud_cli.sh
    # https://docs.cloud.google.com/python/docs/reference/vertexai/latest/vertexai.agent_engines.AgentEngine#vertexai_agent_engines_AgentEngine
    config={
        "display_name": "Agent Runtime",
        "identity_type": types.IdentityType.AGENT_IDENTITY,
        "min_instances": 1,
        "max_instances": 10,
        "resource_limits": {"cpu": "1", "memory": "1Gi"},
        # recommend : 2 * cpu+ 1
        "container_concurrency": 9,
        "staging_bucket": STAGING_BUCKET,
        "extra_packages": ["agent.py"],
        "requirements": [
            # See https://pypi.org/project/google-cloud-aiplatform for the latest version.
            "google-cloud-aiplatform[agent_engines,adk]",
            "pydantic",
            "cloudpickle==3.0",  # new
        ],
        "env_vars": {
            "GOOGLE_CLOUD_LOCATION": "global",
            "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
            # SessionService, MemoryService, ArtifactService
            "ADK_SESSION_SERVICE_URI": "agentengine://",
            "ADK_MEMORY_SERVICE_URI": "agentengine://",
            "ADK_ARTIFACT_SERVICE_URI": STAGING_BUCKET,
            # Telemetry (https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/tracing?hl=ko#write-traces)
            "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
            "OTEL_SEMCONV_STABILITY_OPT_IN": "gen_ai_latest_experimental",
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true",
            # Context-Aware Access 해제 ( Agent Identity 했을 때, 401 UNAUTHENTICATED 오류 나는 경우)
            # https://docs.cloud.google.com/iam/docs/auth-agent-own-identity?hl=ko#opt-out-caa
            # https://docs.cloud.google.com/iam/docs/troubleshoot-auth-manager?hl=ko#401-error
            "GOOGLE_API_PREVENT_AGENT_TOKEN_SHARING_FOR_GCP_SERVICES": "False",
        },
        "context_spec": {"memory_bank_config": memory_bank_config},
    },
)

print("\n✅ Deployment successful!")
print(f"Remote Agent Name: {remote_agent.api_resource.name}")
effective_identity = remote_agent.api_resource.spec.effective_identity
print(f"Agent Identity: {effective_identity}")

print("\n[ 🔒 Required IAM Role Assignment Commands ]")
print(
    "# Run the following commands to grant required permissions to the Agent Identity:"
)
print(f'export AGENT_IDENTITY="{effective_identity}"\n')

roles = [
    "roles/aiplatform.viewer",
    "roles/aiplatform.user",
    "roles/serviceusage.serviceUsageConsumer",
    "roles/apptopology.viewer",  # for agent relationship
    "roles/agentregistry.viewer",  # for agent relationship
    "roles/cloudtrace.user",  # for agent trace
    "roles/logging.viewer",  # for agent log
]

for role in roles:
    print(f"gcloud projects add-iam-policy-binding {PROJECT_ID} \\")
    print(f'    --member="principal://$AGENT_IDENTITY" \\')
    print(f'    --role="{role}"')
