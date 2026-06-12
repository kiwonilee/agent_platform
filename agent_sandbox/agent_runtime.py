#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv, dotenv_values
import vertexai
from vertexai import types
from vertexai.agent_engines import AdkApp


# Locate script parent directory and load configuration from .env
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
load_dotenv(env_path)
env_config = dotenv_values(env_path)

# Resolve required configuration parameters
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = "us-central1"
STAGING_BUCKET = "gs://adk-sandbox-bucket"

# Initialize the Agent Platform client with v1beta1 API
print(f"Initializing Vertex AI Client (Project: {PROJECT_ID}, Location: {LOCATION})...")
client = vertexai.Client(
    project=PROJECT_ID,
    location=LOCATION,
    http_options=dict(api_version="v1beta1")
)

# 1. Create an Agent Platform instance and Code Execution Sandbox
print("Creating Agent Platform instance...")
agent_engine = client.agent_engines.create()
agent_engine_name = agent_engine.api_resource.name

print(f"Creating Agent Engine Sandbox under {agent_engine_name}...")
operation = client.agent_engines.sandboxes.create(
    spec={
        "code_execution_environment": {
            "code_language": "LANGUAGE_PYTHON"
        }
    },
    name=agent_engine_name,
    config=types.CreateAgentEngineSandboxConfig(display_name="Agent Sandbox")
)
sandbox_name = operation.response.name
print(f"✅ Sandbox created successfully! Resource name: {sandbox_name}")

# 2. Deploy Agent to Vertex AI Agent Runtime
print("Wrapping agent in AdkApp...")
os.environ["SANDBOX_RESOURCE_NAME"] = sandbox_name
from agent import data_analyst as agent
app = AdkApp(agent=agent)

remote_app = client.agent_engines.create(
    agent=app,
    config={
        "display_name": "Agent Sandbox",
        "requirements": ["google-adk", "google-cloud-aiplatform[adk,agent_engines]", "cloudpickle", "pydantic"],
        "staging_bucket": STAGING_BUCKET,
        "extra_packages": ["agent.py"],
        "env_vars": {
            "SANDBOX_RESOURCE_NAME": sandbox_name,
            **{k: v for k, v in env_config.items() if k not in ("GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION")},
        },
    },
)

print("\n✅ Deployment successful!")
print(f"Remote Agent Name: {remote_app.api_resource.name}")
