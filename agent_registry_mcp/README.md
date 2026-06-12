# BigQuery MCP Data Science Agent

An enterprise-grade, high-speed **Single-Agent Data Science Architect** built on the Google **ADK (Agent Development Kit)** framework. This agent directly utilizes the **GCP Agent Registry** and **BigQuery MCP (Model Context Protocol)** toolsets to query enterprise datasets, execute SQL analytics, and generate beautiful summarized reports.

---

## 🚀 Core Features

*   **Managed MCP Integration**: Utilizes the native GCP Agent Registry to resolve and securely attach enterprise BigQuery MCP toolsets in a single, high-speed flow.
*   **Memory Bank Integration**: Supports `PreloadMemoryTool` and `add_session_to_memory_callback` for continuous, cross-session conversational memory on production Agent Engine environments.
*   **Unified Python Environment**: Packaged and optimized via `uv` for seamless, robust dependency resolution and virtual environment management.
*   **Seamless Production Deployment**: Supported by a production-ready Vertex AI Agent Engine (Reasoning Engine) deployment script ([ap_runtime.py](file:///usr/local/google/home/kiwonlee/workspace/agents/bq_mcp_agent/ap_runtime.py)).

---

## 📁 Repository Directory Layout

```
bq_mcp_agent/
├── README.md               # Developer manual and instructions
├── pyproject.toml          # Python package and dependency configurations
├── uv.lock                 # Locked dependencies
├── .env.template           # Template for local environment variables
├── .env                    # Local environment variables (gitignored)
├── __init__.py             # Exposes app and root_agent
├── agent.py                # Single-Agent Data Science definition
└── ap_runtime.py           # Production one-click Vertex AI Agent Runtime deployment script
```

---

## ⚙️ Setup & Configuration

### 1. Authentication Scopes (Crucial)
This agent interacts with the **GCP Agent Registry** to resolve MCP toolsets. When authenticating Application Default Credentials (ADC) locally, you **must** request the `cloud-platform` scope to avoid `403 Forbidden (ACCESS_TOKEN_SCOPE_INSUFFICIENT)` errors:

```bash
gcloud auth application-default login --scopes=https://www.googleapis.com/auth/cloud-platform
```

### 2. Environment File (`.env`)
Copy the `.env.template` to `.env` in the root of `bq_mcp_agent/` and configure your GCP project variables:

```bash
cp .env.template .env
```

Your `.env` file should be configured with your GCP project variables and target model:

```ini
# Project configurations
GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
GOOGLE_CLOUD_LOCATION="global"
GOOGLE_GENAI_USE_VERTEXAI=TRUE

# Disable mTLS to bypass local OpenSSL decoding issues during deployment
GOOGLE_API_USE_CLIENT_CERTIFICATE="false"
GOOGLE_API_USE_MTLS_ENDPOINT="never"
```

### 3. Dependency Resolution
Resolve and lock all ADK, GCP, and MCP dependencies using `uv`:

```bash
uv sync
source .venv/bin/activate
```

---

## 💻 Execution Commands

Run all command variants directly from the `bq_mcp_agent/` root directory:

### A. Launch Interactive CLI Mode
To boot up a real-time conversational command-line session directly inside your terminal, run:
```bash
uv run adk run .
```

### B. Launch the Developer Web UI
To launch the background FastAPI server and interact via the Web UI interface:
```bash
uv run adk web .
```
Once initialized, navigate your browser to the URL printed in the terminal (usually `http://127.0.0.1:8086/dev-ui/`).

---

## 🚀 Gemini Enterprise Agent Runtime Deployment (Vertex AI Agent Engine)

For serverless, managed API deployments, you can upload this Data Science Orchestrator Agent to **Vertex AI Agent Engine (Reasoning Engine)**.

### 1. Provision IAM Scopes for Agent Identity
When deploying with Agent Identity (`identity_type=AGENT_IDENTITY`), Google Cloud automatically generates a read-only, system-attested principal identifier for your Agent Runtime instance upon creation:
`principal://iam.googleapis.com/projects/{PROJECT_NUMBER}/locations/global/workloadIdentityPools/...`

Grant the necessary BigQuery, Vertex AI, and Storage Admin scopes to your project's Agent Engine Workload Identity Pool or directly via your Google Cloud console to authorize your deployed Agent to read BigQuery tables and call Gemini.

### 2. Execute the Deployment Script
Once `.env` configurations are finalized, execute the dedicated [ap_runtime.py](file:///usr/local/google/home/kiwonlee/workspace/agents/bq_mcp_agent/ap_runtime.py) script with `uv`:

```bash
uv run python ap_runtime.py
```

Upon successful deployment, the script will print both the remote Resource URI and the runtime's **Effective Identity**. You can use the URI to trigger remote data-science chat sessions:
`projects/{project_number}/locations/us-central1/reasoningEngines/{engine_id}`
