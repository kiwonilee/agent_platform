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

# Load environment variables conditionally (do not overwrite variables already defined in the shell)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/.env" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line//[[:space:]]/}" ]] && continue
    if [[ "$line" =~ ^([A-Za-z0-9_]+)=(.*)$ ]]; then
      key="${BASH_REMATCH[1]}"
      val="${BASH_REMATCH[2]}"
      val="${val#\"}"
      val="${val%\"}"
      if [ -z "${!key}" ]; then
        export "$key"="$val"
      fi
    fi
  done < "$SCRIPT_DIR/.env"
fi

# Function to run test for a specific agent type and ID
run_test() {
  local id="$1"
  local type="$2"
  local message=""

  case "$type" in
    "agent_registry"|"agent-registry"|"agent-registry-mcp")
      message="현재 빅쿼리의 dataset 리스트 알려줘."
      ;;
    "agent_sandbox"|"agent-sandbox")
      message="1부터 100까지의 소수(Prime numbers)를 구하는 파이썬 코드를 작성하고 실행 결과를 알려줘."
      ;;
    "skill_registry"|"skill-registry")
      message="GKE 의 Cluster Upgrade 에 대한 Best Practice 에 대해서 알려줘"
      ;;
    "agent_runtime"|"agent-runtime")
      message="뉴욕의 현재 날씨와 현재 시간을 알려줘."
      ;;
    *)
      message="뉴욕의 현재 날씨와 현재 시간을 알려줘."
      ;;
  esac

  echo "====================================================================="
  echo "🔍 Starting test for $type (ID: $id)"
  echo "💬 Message: \"$message\""
  echo "====================================================================="

  echo "1️⃣ Creating Session..."
  local session_resp
  session_resp=$(curl -s -X POST \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/us-central1/reasoningEngines/${id}:query" \
    -d '{
      "class_method": "create_session",
      "input": {
        "user_id": "test_user"
      }
    }')

  local session_id
  if command -v jq &>/dev/null; then
    session_id=$(echo "$session_resp" | jq -r '.output.id // empty')
  else
    session_id=$(echo "$session_resp" | grep -o '"id": *"[^"]*"' | head -n1 | cut -d'"' -f4)
  fi

  if [ -z "$session_id" ] || [ "$session_id" == "null" ]; then
    echo "❌ Error: Failed to create session. Response:"
    echo "$session_resp"
    return 1
  fi

  echo "✅ Session created successfully: $session_id"
  echo ""

  echo "2️⃣ Sending query message (streaming response)..."
  curl -s -X POST \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/us-central1/reasoningEngines/${id}:streamQuery" \
    -d '{
      "class_method": "async_stream_query",
      "input": {
        "user_id": "test_user",
        "session_id": "'"${session_id}"'",
        "message": "'"${MESSAGE:-$message}"'"
      }
    }'
  echo ""
  echo "====================================================================="
  echo "✅ Test for $type completed!"
  echo "====================================================================="
  echo ""
}

# Scenario 1: No arguments - run tests for all defined IDs in .env
if [ $# -eq 0 ]; then
  tested=0
  if [ -n "$AGENT_REGISTRY_ID" ]; then
    run_test "$AGENT_REGISTRY_ID" "agent_registry"
    tested=1
  fi
  if [ -n "$AGENT_SANDBOX_ID" ]; then
    run_test "$AGENT_SANDBOX_ID" "agent_sandbox"
    tested=1
  fi
  if [ -n "$SKILL_REGISTRY_ID" ]; then
    run_test "$SKILL_REGISTRY_ID" "skill_registry"
    tested=1
  fi
  if [ -n "$AGENT_RUNTIME_ID" ]; then
    run_test "$AGENT_RUNTIME_ID" "agent_runtime"
    tested=1
  fi

  if [ $tested -eq 0 ]; then
    echo "Usage: $0 <REASONING_ENGINE_ID> [agent_registry|agent_sandbox|skill_registry|agent_runtime]"
    echo "Or define AGENT_REGISTRY_ID, AGENT_SANDBOX_ID, SKILL_REGISTRY_ID, AGENT_RUNTIME_ID in your .env file to run all."
    exit 1
  fi
  exit 0
fi

# Scenario 2: Two arguments - explicit ID and Type
if [ $# -eq 2 ]; then
  run_test "$1" "$2"
  exit 0
fi

# Scenario 3: One argument - could be explicit ID (runs default runtime test) OR Type (if defined in env)
if [ $# -eq 1 ]; then
  # Check if argument is a number (ID)
  if [[ "$1" =~ ^[0-9]+$ ]]; then
    run_test "$1" "agent_runtime"
  else
    # It is a type name
    type="$1"
    # Resolve env var name
    case "$type" in
      "agent_registry"|"agent-registry"|"agent-registry-mcp")
        id="$AGENT_REGISTRY_ID"
        ;;
      "agent_sandbox"|"agent-sandbox")
        id="$AGENT_SANDBOX_ID"
        ;;
      "skill_registry"|"skill-registry")
        id="$SKILL_REGISTRY_ID"
        ;;
      "agent_runtime"|"agent-runtime")
        id="$AGENT_RUNTIME_ID"
        ;;
    esac

    if [ -z "$id" ]; then
      echo "❌ Error: ID for agent type '$type' is not defined in .env."
      echo "Please specify it like: $0 <REASONING_ENGINE_ID> $type"
      exit 1
    fi
    run_test "$id" "$type"
  fi
  exit 0
fi
