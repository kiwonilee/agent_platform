import os
import vertexai

PROJECT_ID = "gcp-sandbox-kwlee"
locations = ["global", "us-central1"]

for loc in locations:
    print(f"\n--- Location: {loc} ---")
    client = vertexai.Client(project=PROJECT_ID, location=loc)
    api_client = client.agent_engines.sandboxes._api_client
    print("base_url:", getattr(api_client._http_options, "base_url", None))
    try:
        res = list(client.agent_engines.sandboxes.list(name=f"projects/{PROJECT_ID}/locations/{loc}"))
        print(f"List Success! Found {len(res)} sandboxes.")
    except Exception as e:
        print(f"List Error: {type(e)} - {e}")
