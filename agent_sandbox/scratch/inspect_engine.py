import vertexai
from vertexai.preview import reasoning_engines

PROJECT_ID = "gcp-sandbox-kwlee"
LOCATION = "us-central1"
ENGINE_ID = "8005964725034680320"

vertexai.init(project=PROJECT_ID, location=LOCATION)

print(f"Loading reasoning engine {ENGINE_ID}...")
remote_agent = reasoning_engines.ReasoningEngine(
    f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ENGINE_ID}"
)

print("Attributes of remote_agent:")
for attr in dir(remote_agent):
    if not attr.startswith("__"):
        print(f" - {attr}: {type(getattr(remote_agent, attr))}")
