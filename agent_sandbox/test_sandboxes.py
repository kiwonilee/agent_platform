import os
import vertexai
from vertexai import types

PROJECT_ID = "gcp-sandbox-kwlee"
locations = ["us-central1", "global", "us-east4", "europe-west1"]

print("Testing locations for sandboxes...")
for loc in locations:
    print(f"\n--- Testing Location: {loc} ---")
    try:
        client = vertexai.Client(project=PROJECT_ID, location=loc)
        parent = f"projects/{PROJECT_ID}/locations/{loc}"
        print(f"Listing sandboxes under {parent}...")
        res = list(client.agent_engines.sandboxes.list(name=parent))
        print(f"Success! Found {len(res)} sandboxes.")
    except Exception as e:
        print(f"Error listing in {loc}: {type(e)} - {e}")
