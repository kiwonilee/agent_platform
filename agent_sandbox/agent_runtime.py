#!/usr/bin/env python3
import os
import sys

# Prevent environment variables from overriding explicit SDK location parameters
os.environ.pop("GOOGLE_CLOUD_LOCATION", None)

import vertexai
from vertexai import types
from vertexai.agent_engines import AdkApp

# Configuration parameters
PROJECT_ID = "gcp-sandbox-kwlee"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://adk-sandbox-bucket"

# Initialize the Agent Platform client
print(f"Initializing Vertex AI Client (Project: {PROJECT_ID}, Location: {LOCATION})...")
client = vertexai.Client(
    project=PROJECT_ID,
    location=LOCATION
)

# 1. Skip independent Sandbox creation since we are using BuiltInCodeExecutor
print("Using BuiltInCodeExecutor (no managed sandbox pre-creation required)...")

# 2. Import Agent
from agent import data_analyst as agent

print("Wrapping agent in AdkApp...")
adk_app = AdkApp(agent=agent)

# 3. Deploy Agent to Vertex AI Agent Runtime in a single step
remote_app = client.agent_engines.create(
    agent=adk_app,
    config={
        "display_name": "Agent Sandbox",
        "requirements": [
            "google-adk",
            "google-cloud-aiplatform[adk,agent_engines]",
            "cloudpickle",
            "pydantic"
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
        }
    },
)

print("\n✅ Deployment successful!")
print(f"Remote Agent Name: {remote_app.api_resource.name}")