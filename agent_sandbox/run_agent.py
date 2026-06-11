#!/usr/bin/env python3
"""
Setup script to provision a Vertex AI Agent Engine Sandbox and run/deploy agent.py
Based on: https://adk.dev/integrations/code-exec-agent-runtime/#use-the-tool
"""

import os
import sys
import argparse
import subprocess
from dotenv import load_dotenv

def setup_vertex_client(project_id, location):
    print(f"Initializing Vertex AI Client (Project: {project_id}, Location: {location})...")
    import vertexai
    vertexai.init(project=project_id, location=location)
    return vertexai.Client(project=project_id, location=location)

def create_sandbox(client, project_id, location, display_name):
    print(f"Creating Agent Engine Sandbox '{display_name}'...")
    parent = f"projects/{project_id}/locations/{location}"
    
    operation = client.agent_engines.sandboxes.create(
        name=parent,
        config={
            "display_name": display_name
        },
        spec={
            "code_execution_environment": {
                "code_language": "LANGUAGE_PYTHON"
            }
        }
    )
    print("Waiting for sandbox creation to complete (this might take a few minutes)...")
    sandbox = operation.result()
    print(f"✅ Sandbox created successfully! Resource name: {sandbox.name}")
    return sandbox.name

def update_env_file(script_dir, sandbox_resource_name):
    # Save the sandbox resource name to local .env
    env_file = os.path.join(script_dir, ".env")
    lines = []
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            lines = f.readlines()
            
    # Remove any existing definition of SANDBOX_RESOURCE_NAME
    lines = [line for line in lines if not line.startswith("SANDBOX_RESOURCE_NAME=")]
    lines.append(f'SANDBOX_RESOURCE_NAME="{sandbox_resource_name}"\n')
    
    with open(env_file, "w") as f:
        f.writelines(lines)
    print(f"Updated SANDBOX_RESOURCE_NAME in {env_file}")

def main():
    parser = argparse.ArgumentParser(description="Setup Sandbox and run ADK Agent")
    parser.add_argument("--project_id", type=str, help="GCP Project ID (overrides env)")
    parser.add_argument("--location", type=str, help="GCP Resource Location (overrides env)")
    parser.add_argument("--sandbox_name", type=str, default="data-analyst-sandbox", help="Sandbox Display Name")
    parser.add_argument("--deploy", action="store_true", help="Deploy Agent to Vertex AI Agent Runtime instead of running locally")
    
    args = parser.parse_args()
    
    # Locate paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load env files
    load_dotenv(os.path.join(script_dir, ".env"))
    load_dotenv(os.path.join(script_dir, "..", ".env"))
    
    # Resolve GCP Project and Location
    project_id = args.project_id or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
    location = args.location or os.getenv("GCP_RESOURCES_LOCATION") or os.getenv("LOCATION") or "us-central1"
    
    if not project_id:
        print("Error: GOOGLE_CLOUD_PROJECT or PROJECT_ID environment variable is not set.", file=sys.stderr)
        print("Please define it in your .env file or pass via --project_id.", file=sys.stderr)
        sys.exit(1)
        
    client = setup_vertex_client(project_id, location)
    
    # 1. Create code execution sandbox
    sandbox_name = create_sandbox(client, project_id, location, args.sandbox_name)
    
    # 2. Update env configuration
    update_env_file(script_dir, sandbox_name)
    
    # 3. Execution
    if args.deploy:
        print("\nDeploying agent to Vertex AI Agent Runtime...")
        # (Optional deployment config similar to other project runtime files)
        from vertexai.agent_engines import AdkApp
        # Import target agent
        sys.path.insert(0, script_dir)
        from agent import data_analyst
        
        adk_app = AdkApp(app=data_analyst)
        
        # Build requirements list
        requirements_list = [
            "google-adk[extensions]>=0.1.0",
            "google-cloud-aiplatform[agent_engines]>=1.153.0"
        ]
        
        remote_agent = client.agent_engines.create(
            agent=adk_app,
            config={
                "display_name": "Sandbox Data Analyst Agent",
                "description": "Data Analyst Agent with Sandboxed Python execution",
                "requirements": requirements_list,
                "env_vars": {
                    "SANDBOX_RESOURCE_NAME": sandbox_name,
                    "GOOGLE_CLOUD_PROJECT": project_id
                }
            }
        )
        print(f"✅ Successfully deployed to Agent Runtime! Resource name: {remote_agent.api_resource.name}")
    else:
        # Run local interactive session
        print("\nStarting ADK interactive session via 'adk run'...")
        env = os.environ.copy()
        env["SANDBOX_RESOURCE_NAME"] = sandbox_name
        env["GOOGLE_CLOUD_PROJECT"] = project_id
        
        try:
            subprocess.run(["adk", "run", "."], cwd=script_dir, env=env)
        except FileNotFoundError:
            print("\nError: 'adk' command-line tool not found.", file=sys.stderr)
            print("Please run: pip install google-adk", file=sys.stderr)
            print(f"Alternatively, you can manually run: SANDBOX_RESOURCE_NAME=\"{sandbox_name}\" adk run .", file=sys.stderr)

if __name__ == "__main__":
    main()
