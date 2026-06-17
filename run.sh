#!/bin/bash
set -eo pipefail

# Get current script directory to run sub-deployments reliably
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Determine Google Cloud Project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
  PROJECT_ID="gcp-sandbox-kwlee"
fi
echo "Using Google Cloud Project ID: $PROJECT_ID"

# Export GOOGLE_CLOUD_PROJECT so Python client libraries know which project to target
export GOOGLE_CLOUD_PROJECT="$PROJECT_ID"
export GCP_RESOURCES_LOCATION="us-central1"

# 2. Determine unique GCS Staging Bucket name and create it if missing
CLEAN_PROJECT_ID=$(echo "$PROJECT_ID" | tr '_' '-')
export STAGING_BUCKET_URI="gs://adk-sandbox-bucket-${CLEAN_PROJECT_ID}"
echo "Using GCS Staging Bucket: $STAGING_BUCKET_URI"

if ! gcloud storage buckets describe "$STAGING_BUCKET_URI" --project="$PROJECT_ID" &>/dev/null; then
  echo "Staging bucket $STAGING_BUCKET_URI does not exist. Creating it in us-central1..."
  gcloud storage buckets create "$STAGING_BUCKET_URI" \
    --project="$PROJECT_ID" \
    --location="us-central1"
  echo "✅ Staging bucket created successfully!"
else
  echo "✅ Staging bucket already exists."
fi

# 3. Generate .env file from template and copy to each directory
echo "Generating .env file from .env.template..."
sed -e "s|\${PROJECT_ID}|${PROJECT_ID}|g" \
    -e "s|\${STAGING_BUCKET_URI}|${STAGING_BUCKET_URI}|g" \
    "$SCRIPT_DIR/.env.template" > "$SCRIPT_DIR/.env"

echo "Distributing .env files to agent packages..."
cp "$SCRIPT_DIR/.env" "$SCRIPT_DIR/agent_registry/.env"
cp "$SCRIPT_DIR/.env" "$SCRIPT_DIR/agent_sandbox/.env"
cp "$SCRIPT_DIR/.env" "$SCRIPT_DIR/skill_registry/.env"
cp "$SCRIPT_DIR/.env" "$SCRIPT_DIR/agent_runtime/.env"
echo "✅ .env files distributed successfully!"

# Determine Python command (force Python 3.11 to match Vertex AI Reasoning Engine runtime version)
if command -v uv &> /dev/null; then
  PYTHON_CMD="uv run --python 3.11 python"
else
  PYTHON_CMD="python3.11"
  if ! command -v python3.11 &>/dev/null; then
    PYTHON_CMD="python3"
  fi
fi
echo "Using Python command: $PYTHON_CMD"

# Redundant SCRIPT_DIR definition removed

# -----------------------------------------------------------------------------
# 0. Enable Required GCP APIs
# -----------------------------------------------------------------------------
echo "====================================================================="
echo "⚙️ Enabling Required Google Cloud APIs..."
echo "====================================================================="
gcloud services enable \
  agentregistry.googleapis.com \
  aiplatform.googleapis.com \
  apphub.googleapis.com \
  apptopology.googleapis.com \
  apigeeregistry.googleapis.com \
  iamconnectors.googleapis.com \
  iap.googleapis.com \
  modelarmor.googleapis.com \
  networksecurity.googleapis.com \
  networkservices.googleapis.com \
  observability.googleapis.com \
  saasservicemgmt.googleapis.com \
  securitycenter.googleapis.com \
  texttospeech.googleapis.com \
  --project="$PROJECT_ID"
echo "✅ APIs enabled successfully!"

# -----------------------------------------------------------------------------
# 1. Deploy agent_registry
# -----------------------------------------------------------------------------
echo "====================================================================="
echo "🚀 Deploying 'agent_registry'..."
echo "====================================================================="
(
  cd "$SCRIPT_DIR/agent_registry"
  DEPLOY_OUT=$($PYTHON_CMD agent_runtime.py 2>&1 | tee /dev/stderr)
  
  EFFECTIVE_IDENTITY=$(echo "$DEPLOY_OUT" | grep "^Agent Identity:" | awk '{print $3}')
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
    echo "🎉 IAM role assignment completed for agent_registry!"
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
  DEPLOY_OUT=$($PYTHON_CMD agent_runtime.py 2>&1 | tee /dev/stderr)
  
  EFFECTIVE_IDENTITY=$(echo "$DEPLOY_OUT" | grep "^Agent Identity:" | awk '{print $3}')
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

# -----------------------------------------------------------------------------
# 4. Deploy agent_runtime
# -----------------------------------------------------------------------------
echo "====================================================================="
echo "🚀 Deploying 'agent_runtime'..."
echo "====================================================================="
(
  cd "$SCRIPT_DIR/agent_runtime"
  DEPLOY_OUT=$($PYTHON_CMD agent_runtime.py 2>&1 | tee /dev/stderr)
  
  EFFECTIVE_IDENTITY=$(echo "$DEPLOY_OUT" | grep "^Agent Identity:" | awk '{print $3}')
  if [ -n "$EFFECTIVE_IDENTITY" ]; then
    echo "✅ Found Agent Identity: $EFFECTIVE_IDENTITY"
    echo "🔒 Granting required IAM permissions to principal://${EFFECTIVE_IDENTITY}..."
    for role in \
      "roles/aiplatform.user"
    do
      gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="principal://${EFFECTIVE_IDENTITY}" \
        --role="$role"
    done
    echo "🎉 IAM role assignment completed for agent_runtime!"
  else
    echo "⚠️ Warning: Could not find Agent Identity in deployment output. Skipping IAM bindings."
  fi
)

echo "====================================================================="
echo "✨ All deployments and IAM configurations completed successfully!"
echo "====================================================================="
