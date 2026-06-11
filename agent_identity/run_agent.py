#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv
import vertexai
from vertexai import types
from vertexai.agent_engines import AdkApp

# Locate script parent directory and load configuration from .env
script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, "..", ".env"))

# Resolve required configuration parameters
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GCP_RESOURCES_LOCATION")

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
        "display_name": "running-agent-with-identity",
        "identity_type": types.IdentityType.AGENT_IDENTITY,
        "requirements": ["google-cloud-aiplatform[adk,agent_engines]"],
        # "staging_bucket": staging_bucket_uri,
    },
)

print("\n✅ Deployment successful!")
print(f"Remote Agent Name: {remote_app.api_resource.name}")
print(f"Effective Identity: {remote_app.api_resource.spec.effective_identity}")