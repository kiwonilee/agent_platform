#!/usr/bin/env python3
import os
import sys

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import vertexai
from vertexai.agent_engines import AdkApp

# Prevent environment variables from overriding explicit SDK location parameters
os.environ.pop("GOOGLE_CLOUD_LOCATION", None)

PROJECT_ID = "gcp-sandbox-kwlee"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://adk-sandbox-bucket"
ENGINE_ID = "8005964725034680320"

# Target engine name
container_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ENGINE_ID}"

print(f"Initializing Vertex AI Client (Project: {PROJECT_ID}, Location: {LOCATION})...")
client = vertexai.Client(
    project=PROJECT_ID,
    location=LOCATION
)

# Fetch current engine to get its sandbox name or configurations if needed
print(f"Fetching existing AgentEngine container: {container_name}...")
engine = client.agent_engines.get(name=container_name)

# Extract existing environment variables from the fetched engine
env_vars = {}
if hasattr(engine.api_resource.spec, "deployment_spec") and engine.api_resource.spec.deployment_spec is not None:
    if hasattr(engine.api_resource.spec.deployment_spec, "env") and engine.api_resource.spec.deployment_spec.env is not None:
        for env_var in engine.api_resource.spec.deployment_spec.env:
            env_vars[env_var.name] = env_var.value

print(f"Existing environment variables: {env_vars}")

# Inject SANDBOX_RESOURCE_NAME locally if present, so the agent pickling process receives it
sandbox_resource_name = env_vars.get("SANDBOX_RESOURCE_NAME")
if sandbox_resource_name:
    print(f"Injecting local SANDBOX_RESOURCE_NAME = {sandbox_resource_name}")
    os.environ["SANDBOX_RESOURCE_NAME"] = sandbox_resource_name

# Now import the agent
from agent import root_agent as agent

# Wrap agent in AdkApp
print("Wrapping agent in AdkApp...")
adk_app = AdkApp(agent=agent)

# Deploy Agent to Vertex AI Agent Runtime by updating the container
print("Updating Agent Runtime container with patched agent...")
remote_agent = client.agent_engines.update(
    name=container_name,
    agent=adk_app,
    config={
        "display_name": "Agent Sandbox",
        "requirements": [
            "google-adk==2.2.0",
            "google-cloud-aiplatform[adk,agent_engines]==1.157.0",
            "pydantic==2.13.4",
            "cloudpickle==3.1.2"
        ],
        "staging_bucket": STAGING_BUCKET,
        "extra_packages": ["agent.py"],
        "env_vars": env_vars  # Use extracted environment variables
    },
)

print("\n✅ Redeployment successful!")
print(f"Remote Agent Name: {remote_agent.api_resource.name}")
