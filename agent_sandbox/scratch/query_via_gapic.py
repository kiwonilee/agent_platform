from google.cloud import aiplatform_v1beta1
from google.protobuf import struct_pb2

client = aiplatform_v1beta1.ReasoningEngineExecutionServiceClient(
    client_options={"api_endpoint": "us-central1-aiplatform.googleapis.com"}
)

name = "projects/458778613248/locations/us-central1/reasoningEngines/8005964725034680320"

input_struct = struct_pb2.Struct()
input_struct.update({
    "message": "Please write a Python script to calculate the sum of integers from 1 to 100, execute it, and tell me the result.",
    "user_id": "test-user-id"
})

# stream_query_reasoning_engine
print("Calling stream_query_reasoning_engine...")
try:
    response_stream = client.stream_query_reasoning_engine(
        request={
            "name": name,
            "input": input_struct,
            "class_method": "stream_query",
        }
    )
    for response in response_stream:
        # HttpBody response
        print("Response chunk content:", response.data.decode("utf-8"))
except Exception as e:
    import traceback
    traceback.print_exc()
