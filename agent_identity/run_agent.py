#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv
import vertexai
from vertexai import types
from vertexai.agent_engines import AdkApp
from agent import root_agent as agent


# Locate script parent directory and load configuration from .env
script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, "..", ".env"))

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
        "requirements": ["google-cloud-aiplatform[adk,agent_engines]", "cloudpickle", "pydantic"],
        "staging_bucket": STAGING_BUCKET,
        "extra_packages": ["agent.py"],
    },
)

print("\n✅ Deployment successful!")
print(f"Remote Agent Name: {remote_app.api_resource.name}")
print(f"Effective Identity: {remote_app.api_resource.spec.effective_identity}")
