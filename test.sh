#!/bin/bash
set -eo pipefail

# Determine project settings
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
  echo "❌ Error: Google Cloud Project ID is not configured."
  echo "Please run 'gcloud config set project [PROJECT_ID]' first."
  exit 1
fi

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
ACCESS_TOKEN=$(gcloud auth print-access-token)

# Parse Arguments
REASONING_ENGINE_ID="$1"
AGENT_TYPE="$2"

if [ -z "$REASONING_ENGINE_ID" ]; then
  echo "Usage: $0 <REASONING_ENGINE_ID> [agent_registry|agent_sandbox|skill_registry|agent_runtime]"
  exit 1
fi

# Set sample messages
case "$AGENT_TYPE" in
  "agent_registry"|"agent-registry"|"agent-registry-mcp")
    MESSAGE="현재 빅쿼리의 dataset 리스트 알려줘."
    ;;
  "agent_sandbox"|"agent-sandbox")
    MESSAGE="1부터 100까지의 소수(Prime numbers)를 구하는 파이썬 코드를 작성하고 실행 결과를 알려줘."
    ;;
  "skill_registry"|"skill-registry")
    MESSAGE="GKE 의 Cluster Upgrade 에 대한 Best Practice 에 대해서 알려줘"
    ;;
  "agent_runtime"|"agent-runtime")
    MESSAGE="뉴욕의 현재 날씨와 현재 시간을 알려줘."
    ;;
  *)
    echo "No matching agent type specified or invalid type: '$AGENT_TYPE'"
    echo "Available types: agent_registry, agent_sandbox, skill_registry, agent_runtime"
    echo "Defaulting to agent_runtime weather/time query..."
    MESSAGE="뉴욕의 현재 날씨와 현재 시간을 알려줘."
    ;;
esac

echo "========================================="
echo "🔍 Starting test for Agent ID: $REASONING_ENGINE_ID"
echo "💬 Message: \"$MESSAGE\""
echo "========================================="

# 1. Create Session
echo "1️⃣ Creating Session..."
SESSION_RESP=$(curl -s -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}:query" \
  -d '{
    "class_method": "create_session",
    "input": {
      "user_id": "test_user"
    }
  }')

# Extract Session ID using jq if available, otherwise fallback to grep/cut
if command -v jq &>/dev/null; then
  SESSION_ID=$(echo "$SESSION_RESP" | jq -r '.output.id // empty')
else
  SESSION_ID=$(echo "$SESSION_RESP" | grep -o '"id": *"[^"]*"' | head -n1 | cut -d'"' -f4)
fi

if [ -z "$SESSION_ID" ] || [ "$SESSION_ID" == "null" ]; then
  echo "❌ Error: Failed to create session. Response:"
  echo "$SESSION_RESP"
  exit 1
fi

echo "✅ Session created successfully: $SESSION_ID"
echo ""

# 2. Query Agent (streamQuery)
echo "2️⃣ Sending query message (streaming response)..."
curl -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}:streamQuery" \
  -d '{
    "class_method": "async_stream_query",
    "input": {
      "user_id": "test_user",
      "session_id": "'"${SESSION_ID}"'",
      "message": "'"${MESSAGE}"'"
    }
  }'

echo ""
echo "========================================="
echo "✅ Test completed!"
echo "========================================="
