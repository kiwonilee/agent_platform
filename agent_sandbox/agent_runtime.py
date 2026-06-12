#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv, dotenv_values
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

# create an Agent Platform instance
print("Creating Agent Platform instance...")
agent_engine = client.agent_engines.create()
agent_engine_name = agent_engine.api_resource.name

# create Agent Sandbox
# https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/sandbox/code-execution-quickstart#create_a_sandbox
print(f"Creating Agent Sandbox under {agent_engine_name}...")
operation = client.agent_engines.sandboxes.create(
    spec={
        "code_execution_environment": {            
            "code_language": "LANGUAGE_PYTHON",  # 실행할 프로그래밍 언어   
            "machine_config": "MACHINE_CONFIG_VCPU4_RAM4GIB", # 컴퓨팅 자원 설정
        }
    },
    name=agent_engine_name,
    config=types.CreateAgentEngineSandboxConfig(display_name="Agent Sandbox")
)
sandbox_name = operation.response.name
print(f"✅ Sandbox created successfully! Resource name: {sandbox_name}")

# Use the proper wrapper class for your Agent Framework
print("Wrapping agent in AdkApp...")
adk_app = AdkApp(agent=agent)

# Deploy Agent to Vertex AI Agent Runtime
remote_app = client.agent_engines.create(
    agent=adk_app,
    config={
        "display_name": "Agent Sandbox",
        "requirements": [
            "google-adk",
            "google-cloud-aiplatform[adk,agent_engines]",
            "cloudpickle",
            "pydantic"],
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
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "EVENT_ONLY"
        }
    },
)

print("\n✅ Deployment successful!")
print(f"Remote Agent Name: {remote_app.api_resource.name}")
