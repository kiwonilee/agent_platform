#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv, dotenv_values
import vertexai
from vertexai import types
from vertexai.agent_engines import AdkApp
from agent import root_agent as agent


# Locate script parent directory and load configuration from .env
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
load_dotenv(env_path)
env_config = dotenv_values(env_path)

# Resolve required configuration parameters
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = "us-central1"
STAGING_BUCKET = "gs://adk-sandbox-bucket"

# Initialize the Agent Platform client with v1beta1 API for agent identity support
print(f"Initializing Vertex AI Client (Project: {PROJECT_ID}, Location: {LOCATION})...")
client = vertexai.Client(
    project=PROJECT_ID,
    location=LOCATION,
    http_options=dict(api_version="v1beta1")
)

# Use the proper wrapper class for your Agent Framework
print("Wrapping agent in AdkApp...")
app = AdkApp(agent=agent)

remote_app = client.agent_engines.create(
    agent=app,
    config={
        "display_name": "Agent Identity",
        "identity_type": types.IdentityType.AGENT_IDENTITY,
        "requirements": ["google-adk[agent-identity]", "google-cloud-aiplatform[agent_engines]", "cloudpickle", "pydantic"],
        "staging_bucket": STAGING_BUCKET,
        "extra_packages": ["agent.py"],
        "env_vars": {
            # https://docs.cloud.google.com/iam/docs/auth-agent-own-identity?hl=ko#opt-out-caa
            # https://docs.cloud.google.com/iam/docs/troubleshoot-auth-manager?hl=ko#401-error
            "GOOGLE_API_PREVENT_AGENT_TOKEN_SHARING_FOR_GCP_SERVICES": "False",
            **{k: v for k, v in env_config.items() if k not in ("GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION")},
        },
    },
)

print("\n✅ Deployment successful!")
print(f"Remote Agent Name: {remote_app.api_resource.name}")
print(f"Effective Identity: {remote_app.api_resource.spec.effective_identity}")
