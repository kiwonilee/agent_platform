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
    config={
        "display_name": "Agent Registry",
        # "service_account": service_account_email,
        "identity_type": types.IdentityType.AGENT_IDENTITY,
        "requirements": [
            "google-adk[agent-identity,a2a]>=2.2.0",
            "a2a-sdk",
            "google-cloud-aiplatform[agent_engines]",
            "cloudpickle",
            "pydantic",
            "mcp",
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
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "EVENT_ONLY",
            # Context-Aware Access 해제 ( Agent Identity 했을 때, 401 UNAUTHENTICATED 오류 나는 경우)
            # https://docs.cloud.google.com/iam/docs/auth-agent-own-identity?hl=ko#opt-out-caa
            # https://docs.cloud.google.com/iam/docs/troubleshoot-auth-manager?hl=ko#401-error
            "GOOGLE_API_PREVENT_AGENT_TOKEN_SHARING_FOR_GCP_SERVICES": "False"
        }
    }
)

print("\n✅ Deployment successful!")
print(f"Remote Agent Name: {remote_agent.api_resource.name}")
effective_identity = remote_agent.api_resource.spec.effective_identity
print(f"Agent Identity: {effective_identity}")

print("\n[ 🔒 Required IAM Role Assignment Commands ]")
print("# Grant BigQuery query/view, Vertex AI call, and Storage permissions to the Agent Identity:")
for role in [
    "roles/bigquery.dataViewer",
    "roles/bigquery.jobUser",    
    "roles/storage.objectAdmin",
    "roles/aiplatform.user",
    "roles/mcp.toolUser"
]:
    print(f"gcloud projects add-iam-policy-binding {PROJECT_ID} \\")
    print(f"    --member=\"principal://{effective_identity}\" \\")
    print(f"    --role=\"{role}\"")
