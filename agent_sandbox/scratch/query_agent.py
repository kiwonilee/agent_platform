import vertexai
from vertexai.preview import reasoning_engines

PROJECT_ID = "gcp-sandbox-kwlee"
LOCATION = "us-central1"
ENGINE_ID = "8005964725034680320"

vertexai.init(project=PROJECT_ID, location=LOCATION)

# Load the deployed reasoning engine
print(f"Loading reasoning engine {ENGINE_ID}...")
remote_agent = reasoning_engines.ReasoningEngine(
    f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ENGINE_ID}"
)

# Test query using the standard .query method
print("Sending test query via .query()...")
try:
    response = remote_agent.query(
        message="Please write a Python script to calculate the sum of integers from 1 to 100, execute it, and tell me the result."
    )
    print("Query Response:", response)
except Exception as e:
    import traceback
    traceback.print_exc()

# Test stream query using the .stream method
print("\nSending test query via .stream()...")
try:
    for event in remote_agent.stream(
        message="Please write a Python script to calculate the sum of integers from 1 to 100, execute it, and tell me the result."
    ):
        print("Stream Event:", event)
except Exception as e:
    import traceback
    traceback.print_exc()
