#!/usr/bin/env python3
"""
Enterprise Skill Registry Administration CLI Tool
Provides focused subcommands: create, list, get, delete, retrieve, and import
for Vertex AI Agent Platform Skill Registry management.
"""

import argparse
import os
import subprocess
import tempfile
import shutil
from datetime import datetime
import vertexai


def list_skills(client):
  """Lists all registered skills in the project region."""
  print("\n====================================================================================")
  print("                   ACTIVE AGENT PLATFORM SKILLS REGISTRY LIST")
  print("====================================================================================")
  pager = client.skills.list()
  count = 0
  for skill in pager:
    print(f"  * Display Name: {skill.display_name}")
    print(f"    Resource URI: {skill.name}")
    print(f"    Description : {skill.description}")
    print("------------------------------------------------------------------------------------")
    count += 1
  print(f"Total registered skills found in region: {count}")
  print("====================================================================================\n")


def create_skill(client, display_name: str, description: str, local_path: str, skill_id: str = None):
  """Registers/Creates a new skill in the registry."""
  if not skill_id:
    # Auto-generate a slug-friendly skill ID
    clean_slug = display_name.lower().replace(" ", "-")
    clean_slug = "".join(c for c in clean_slug if c.isalnum() or c == "-")
    # Truncate to 45 chars max to ensure total length with timestamp is well under 63 chars limit
    clean_slug = clean_slug[:45].rstrip("-")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    skill_id = f"{clean_slug}-{timestamp}"

  print(f"Creating skill '{display_name}' from local path '{local_path}'...")
  created_skill = client.skills.create(
      display_name=display_name,
      description=description,
      config={
          "local_path": local_path,
          "skill_id": skill_id
      }
  )
  print(f"\nSUCCESS: Skill registered successfully!")
  print(f"Resource Name: {created_skill.name}")
  print(f"Display Name : {created_skill.display_name}")
  print(f"Description  : {created_skill.description}")
  return created_skill


def get_skill(client, skill_name_or_id: str, project_id: str, location: str):
  """Gets a single registered skill by its name/ID."""
  if not skill_name_or_id.startswith("projects/"):
    full_resource_name = f"projects/{project_id}/locations/{location}/skills/{skill_name_or_id}"
  else:
    full_resource_name = skill_name_or_id

  print(f"Fetching skill details for: {full_resource_name}...")
  skill = client.skills.get(name=full_resource_name)
  print("\n====================================================================================")
  print("                            SKILL SPEC DETAILS")
  print("====================================================================================")
  print(f"  * Display Name: {skill.display_name}")
  print(f"    Resource URI: {skill.name}")
  print(f"    Description : {skill.description}")
  print("====================================================================================\n")
  return skill


def delete_skill(client, skill_name_or_id: str, project_id: str, location: str):
  """Deletes a registered skill by its name/ID."""
  if not skill_name_or_id.startswith("projects/"):
    full_resource_name = f"projects/{project_id}/locations/{location}/skills/{skill_name_or_id}"
  else:
    full_resource_name = skill_name_or_id

  print(f"Deleting skill: {full_resource_name}...")
  client.skills.delete(name=full_resource_name)
  print(f"SUCCESS: Successfully deleted skill '{skill_name_or_id}'")


def retrieve_skills(client, query: str, top_k: int = 2):
  """Performs semantic RAG search on the registered skills."""
  print(f"Querying skills registry for playbooks matching: '{query}' (top_k={top_k})...")
  response = client.skills.retrieve(
      query=query,
      config={"top_k": top_k}
  )
  print("\n====================================================================================")
  print(f"                      SEMANTIC RETRIEVAL RESULTS FOR: '{query}'")
  print("====================================================================================")
  print(f"Found {len(response.retrieved_skills)} matching skills.")
  for i, retrieved in enumerate(response.retrieved_skills):
    print(f"  [{i+1}] Skill Name : {retrieved.skill_name}")
    print(f"      Description: {retrieved.description}")
    print("------------------------------------------------------------------------------------")
  print("====================================================================================\n")
  return response


# -----------------------------------------------------------------------------
# GitHub Skills Import Helpers
# -----------------------------------------------------------------------------
def download_github_repo(url: str, dest_dir: str):
  """Clones a public GitHub repository into the target destination folder."""
  print(f"\nCloning GitHub repository '{url}' into temporary folder '{dest_dir}'...")
  # Use git clone with depth=1 for maximum speed and efficiency
  subprocess.run(["git", "clone", "--depth=1", url, dest_dir], check=True, capture_output=True)


def parse_skill_md(filepath: str, default_name: str):
  """Parses a standard SKILL.md file to dynamically extract display name and description."""
  display_name = default_name
  description = f"SRE playbook handbook imported from {default_name} playbook."

  if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
      lines = f.readlines()

    # Extract the H1 markdown header as the display name
    for line in lines:
      if line.strip().startswith("# "):
        display_name = line.replace("# ", "").strip()
        break

    # Parse non-empty paragraph lines for description
    paragraphs = []
    current_para = []
    for line in lines:
      stripped = line.strip()
      if stripped.startswith("#"):
        if current_para:
          paragraphs.append(" ".join(current_para))
          current_para = []
      elif stripped:
        current_para.append(stripped)
      else:
        if current_para:
          paragraphs.append(" ".join(current_para))
          current_para = []
    if current_para:
      paragraphs.append(" ".join(current_para))

    # Set description to the first substantial paragraph (excluding headers/titles)
    for p in paragraphs:
      if not p.startswith(display_name) and len(p) > 15:
        description = p
        break

  # Limit description string size to fit registry constraints nicely
  if len(description) > 300:
    description = description[:297] + "..."
  return display_name, description


def import_skills_from_github(client, repo_url: str, sub_path: str = None):
  """Clones a GitHub repo, automatically scans SRE playbooks containing SKILL.md, and registers them."""
  output_dir = tempfile.mkdtemp()
  try:
    download_github_repo(repo_url, output_dir)

    search_path = output_dir
    if sub_path:
      search_path = os.path.join(output_dir, sub_path.lstrip("/"))

    print(f"Scanning for SRE playbooks under path: '{search_path}'...")
    skills_found = []

    # Walk recursively to detect all playbooks containing SKILL.md
    for root, _, files in os.walk(search_path):
      # Skip git folder configurations
      if ".git" in root:
        continue
      if "SKILL.md" in files:
        skill_md_path = os.path.join(root, "SKILL.md")
        folder_name = os.path.basename(root)
        
        display_name, description = parse_skill_md(skill_md_path, folder_name)
        skills_found.append({
            "display_name": display_name,
            "description": description,
            "local_path": root
        })

    if not skills_found:
      print(f"\nNo playbook directories containing 'SKILL.md' were found in path '{repo_url}/{sub_path or ''}'!")
      return

    print(f"\n====================================================================================")
    print(f"               DETECTED {len(skills_found)} PLAYBOOK SKILLS FOR IMPORT")
    print("====================================================================================")
    for s in skills_found:
      print(f"  * Display Name: {s['display_name']}")
      print(f"    Description : {s['description']}")
      print(f"    Local Path  : {s['local_path']}")
      print("------------------------------------------------------------------------------------")
    print("====================================================================================\n")

    # Eagerly register each playbook skill
    for s in skills_found:
      create_skill(client, s["display_name"], s["description"], s["local_path"])

    print(f"\nSUCCESS: All {len(skills_found)} SRE playbooks imported and registered successfully!")

  finally:
    print(f"Cleaning up temporary clone folder '{output_dir}'...")
    shutil.rmtree(output_dir, ignore_errors=True)


def main():
  parser = argparse.ArgumentParser(
      description="Vertex AI Agent Platform Skill Registry Management CLI Tool",
      formatter_class=argparse.RawDescriptionHelpFormatter
  )
  parser.add_argument(
      "--project-id",
      default=os.environ.get("GOOGLE_CLOUD_PROJECT", "gcp-sandbox-kwlee"),
      help="Google Cloud Project ID"
  )
  parser.add_argument(
      "--location",
      default=os.environ.get("GCP_RESOURCES_LOCATION", "us-central1"),
      help="Vertex AI location/region"
  )

  subparsers = parser.add_subparsers(dest="command", required=True, help="Skill Registry Commands")

  # 1. 'list' subcommand
  subparsers.add_parser("list", help="List all registered skills in the project region")

  # 2. 'create' subcommand
  create_parser = subparsers.add_parser("create", help="Register/Create a new skill from local playbook path")
  create_parser.add_argument("--display-name", required=True, help="Display name for the skill")
  create_parser.add_argument("--description", required=True, help="Detailed operational description for the skill")
  create_parser.add_argument("--local-path", required=True, help="Local folder directory containing SKILL.md / playbooks")
  create_parser.add_argument("--skill-id", default=None, help="Optional custom unique slug ID for the skill")

  # 3. 'get' subcommand
  get_parser = subparsers.add_parser("get", help="Retrieve detailed specs of a registered skill")
  get_parser.add_argument("--skill-name", required=True, help="The resource name or raw ID of the skill to fetch")

  # 4. 'delete' subcommand
  delete_parser = subparsers.add_parser("delete", help="Delete a registered skill from the registry")
  delete_parser.add_argument("--skill-name", required=True, help="The resource name or raw ID of the skill to delete")

  # 5. 'retrieve' subcommand
  retrieve_parser = subparsers.add_parser("retrieve", help="Perform RAG semantic search query on registered playbooks")
  retrieve_parser.add_argument("--query", required=True, help="The query string (e.g., 'GKE node upgrade')")
  retrieve_parser.add_argument("--top-k", type=int, default=2, help="Maximum number of semantic matches to fetch")

  # 6. 'import' subcommand (New GitHub Import integration!)
  import_parser = subparsers.add_parser("import", help="Download and register SRE playbooks from a public GitHub repository")
  import_parser.add_argument("--github-url", required=True, help="The public GitHub HTTPS clone URL (e.g., https://github.com/user/repo.git)")
  import_parser.add_argument("--sub-path", default=None, help="Optional subdirectory path inside the repository to restrict the playbook scan")

  args = parser.parse_args()

  # Initialize Vertex AI client
  vertexai.init(project=args.project_id, location=args.location)
  client = vertexai.Client(project=args.project_id, location=args.location)

  # Subcommand multiplexer
  try:
    if args.command == "list":
      list_skills(client)
    elif args.command == "create":
      create_skill(client, args.display_name, args.description, args.local_path, args.skill_id)
    elif args.command == "get":
      get_skill(client, args.skill_name, args.project_id, args.location)
    elif args.command == "delete":
      delete_skill(client, args.skill_name, args.project_id, args.location)
    elif args.command == "retrieve":
      retrieve_skills(client, args.query, args.top_k)
    elif args.command == "import":
      import_skills_from_github(client, args.github_url, args.sub_path)
  except Exception as e:
    print(f"\nERROR: Execution failed: {e}")


if __name__ == "__main__":
  main()