#!/bin/bash

# Configuration
export PROJECT_NUMBER="458778613248"
export REASONING_ENGINE_ID="4389363118023639040"

echo "================================================================="
echo "Testing Sandbox-based Deployed Reasoning Engine: $REASONING_ENGINE_ID"
echo "================================================================="

# 1. Create a session
echo "1. Creating conversation session..."
SESSION_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  https://us-central1-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}:query \
  -d '{
    "class_method": "create_session",
    "input": {
      "user_id": "sandbox_tester"
    }
  }')

echo "Response from Session Creation:"
echo "$SESSION_RESPONSE"

# Extract session ID from the response (using a simple regex/sed since jq might not be installed, or we can use python to extract it safely)
SESSION_ID=$(echo "$SESSION_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('output', {}).get('id', ''))")

if [ -z "$SESSION_ID" ]; then
    echo "❌ Failed to extract Session ID."
    exit 1
fi

echo "✅ Generated Session ID: $SESSION_ID"
echo "-----------------------------------------------------------------"

# 2. Send query involving Python code execution
echo "2. Sending coding/calculation query to sandbox-based agent..."
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  https://us-central1-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}:streamQuery \
  -d '{
    "class_method": "async_stream_query",
    "input": {
      "user_id": "sandbox_tester",
      "session_id": "'"${SESSION_ID}"'",
      "message": "Calculate 10^9 minus 12^5 using python loop, and print the results step by step."
    }
  }'

echo -e "\n\n✅ Sandbox-based reasoning engine verification curl run completed!"
