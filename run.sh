#!/bin/bash
set -eo pipefail

# 1. Determine Google Cloud Project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
  PROJECT_ID="gcp-sandbox-kwlee"
fi
echo "Using Google Cloud Project ID: $PROJECT_ID"

# Determine Python command (use 'uv run python' if uv is available, otherwise 'python3')
if command -v uv &> /dev/null; then
  PYTHON_CMD="uv run python"
else
  PYTHON_CMD="python3"
fi
echo "Using Python command: $PYTHON_CMD"

# Get current script directory to run sub-deployments reliably
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# -----------------------------------------------------------------------------
# 1. Deploy agent_registry_mcp
# -----------------------------------------------------------------------------
echo "====================================================================="
echo "🚀 Deploying 'agent_registry_mcp'..."
echo "====================================================================="
(
  cd "$SCRIPT_DIR/agent_registry_mcp"
  if [ "$PYTHON_CMD" = "uv run python" ]; then
    uv sync
  fi
  DEPLOY_OUT=$($PYTHON_CMD agent_runtime.py 2>&1 | tee /dev/stderr)
  
  EFFECTIVE_IDENTITY=$(echo "$DEPLOY_OUT" | grep "Agent Identity:" | awk '{print $3}')
  if [ -n "$EFFECTIVE_IDENTITY" ]; then
    echo "✅ Found Agent Identity: $EFFECTIVE_IDENTITY"
    echo "🔒 Granting required IAM permissions to principal://${EFFECTIVE_IDENTITY}..."
    for role in \
      "roles/bigquery.dataViewer" \
      "roles/bigquery.jobUser" \
      "roles/storage.objectAdmin" \
      "roles/aiplatform.user" \
      "roles/mcp.toolUser"
    do
      gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="principal://${EFFECTIVE_IDENTITY}" \
        --role="$role"
    done
    echo "🎉 IAM role assignment completed for agent_registry_mcp!"
  else
    echo "⚠️ Warning: Could not find Agent Identity in deployment output. Skipping IAM bindings."
  fi
)

# -----------------------------------------------------------------------------
# 2. Deploy agent_sandbox
# -----------------------------------------------------------------------------
echo "====================================================================="
echo "🚀 Deploying 'agent_sandbox'..."
echo "====================================================================="
(
  cd "$SCRIPT_DIR/agent_sandbox"
  $PYTHON_CMD agent_runtime.py
  echo "🎉 agent_sandbox deployed successfully!"
)

# -----------------------------------------------------------------------------
# 3. Deploy skill_registry
# -----------------------------------------------------------------------------
echo "====================================================================="
echo "🚀 Deploying 'skill_registry'..."
echo "====================================================================="
(
  cd "$SCRIPT_DIR/skill_registry"
  if [ "$PYTHON_CMD" = "uv run python" ]; then
    uv sync
  fi
  DEPLOY_OUT=$($PYTHON_CMD agent_runtime.py 2>&1 | tee /dev/stderr)
  
  EFFECTIVE_IDENTITY=$(echo "$DEPLOY_OUT" | grep "Agent Identity:" | awk '{print $3}')
  if [ -n "$EFFECTIVE_IDENTITY" ]; then
    echo "✅ Found Agent Identity: $EFFECTIVE_IDENTITY"
    echo "🔒 Granting required IAM permissions to principal://${EFFECTIVE_IDENTITY}..."
    for role in \
      "roles/aiplatform.viewer" \
      "roles/aiplatform.user" \
      "roles/serviceusage.serviceUsageConsumer"
    do
      gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="principal://${EFFECTIVE_IDENTITY}" \
        --role="$role"
    done
    echo "🎉 IAM role assignment completed for skill_registry!"
  else
    echo "⚠️ Warning: Could not find Agent Identity in deployment output. Skipping IAM bindings."
  fi
)

echo "====================================================================="
echo "✨ All deployments and IAM configurations completed successfully!"
echo "====================================================================="
