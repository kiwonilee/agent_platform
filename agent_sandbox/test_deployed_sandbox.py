import os
import vertexai
from vertexai.preview.reasoning_engines import ReasoningEngine

PROJECT_ID = "gcp-sandbox-kwlee"
LOCATION = "us-central1"
ENGINE_ID = "4389363118023639040"

print(f"Initializing Vertex AI (Project: {PROJECT_ID}, Location: {LOCATION})...")
vertexai.init(project=PROJECT_ID, location=LOCATION)

print(f"Loading deployed ReasoningEngine: {ENGINE_ID}...")
remote_app = ReasoningEngine(f"projects/458778613248/locations/{LOCATION}/reasoningEngines/{ENGINE_ID}")

print("\nSending query to agent (triggering Python sandbox execution)...")
try:
    # We ask a complex math/data task to force it to use Python code execution
    response = remote_app.query(
        input="Please calculate the factorial of 15 using a python loop, and print each step."
    )
    print("\n--- Agent Response ---")
    print(response)
    print("----------------------")
    print("\n✅ Verification successful!")
except Exception as e:
    print(f"\n❌ Error during query execution: {e}")
