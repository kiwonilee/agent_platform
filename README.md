# Agent Platform

A unified repository containing multiple AI agents and configurations for Vertex AI Agent Engine.



## Environment Setup

The agents require `.env` files in their respective directories containing project configuration (e.g. `PROJECT_ID`, `STAGING_BUCKET_URI`).

You can automatically generate and distribute these files from the template by running `run.sh`, or do it manually:

1. Generate `.env` from the template (replace placeholders with your Google Cloud Project ID and GCS Staging Bucket URI):
   ```bash
   sed -e "s|\${PROJECT_ID}|YOUR_PROJECT_ID|g" \
       -e "s|\${STAGING_BUCKET_URI}|YOUR_STAGING_BUCKET_URI|g" \
       .env.template > .env
   ```

2. Distribute the `.env` file to each agent directory:
   ```bash
   cp .env agent_registry/.env
   cp .env agent_sandbox/.env
   cp .env skill_registry/.env
   cp .env agent_runtime/.env
   ```

## How to Run

To run an agent, execute it from this root directory using `uv run`:

```bash
# Run agent registry
uv run agent_registry/agent_runtime.py

# Run skill registry
uv run skill_registry/agent_runtime.py

# Run agent runtime
uv run agent_runtime/agent_runtime.py

# Run agent sandbox
uv run agent_sandbox/agent_runtime.py
```