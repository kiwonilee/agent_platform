#!/usr/bin/env python3
"""
Skill Registry Tool
Replicated from skill_registry.ipynb
"""

import argparse
import os
import re
import sys
import shutil
import tempfile
import urllib.request
import yaml
import zipfile
from datetime import datetime

import vertexai


class Skill:
  def __init__(self, name: str, description: str, local_skill_dir: str):
    self.name = name
    self.description = description
    self.local_skill_dir = local_skill_dir

  def __str__(self) -> str:
    return f"Skill(name={self.name}, description={self.description}, local_skill_dir={self.local_skill_dir})"


def parse_skill_md(filepath: str) -> tuple[str, str]:
  """Parses SKILL.md file to get the skill name and description."""
  name = "Untitled Skill"
  description = "No description provided."
  try:
    with open(filepath, "r", encoding="utf-8") as f:
      content = f.read()
      if content.startswith("---"):
        end_idx = content.find("---", 3)
        if end_idx != -1:
          yaml_part = content[3:end_idx]
          try:
            data = yaml.safe_load(yaml_part)
            if data:
              name = data.get("name", name)
              description = data.get("description", description)
          except yaml.YAMLError as yaml_e:
            print(f"YAML parsing warning (using fallback): {yaml_e}")
            match_name = re.search(r"^name:\s*(.+)$", yaml_part, re.M)
            if match_name:
              name = match_name.group(1).strip()
            match_desc = re.search(
                r"^description:\s*(?:>-\s*)?(.+)$", yaml_part, re.M
            )
            if match_desc:
              description = match_desc.group(1).strip()
  except IOError as e:
    print(f"Failed to parse {filepath}: {e}")
  return name, description


def get_all_skills_from_dir(repo_dir: str) -> list[Skill]:
  """Returns a list of Skill objects from the given directory."""
  skills = []
  skills_found = 0
  seen_skills = set()
  for root, dirs, files in os.walk(repo_dir):
    lower_files = {f.lower(): f for f in files}
    if "skill.md" in lower_files:
      # Prune subdirectories to avoid deeper recursion in this skill folder.
      dirs[:] = []

      skill_md_filename = lower_files["skill.md"]
      filepath = os.path.join(root, skill_md_filename)

      name, description = parse_skill_md(filepath)

      # De-dupe based on skill name
      if name in seen_skills:
        print(f"Skipping duplicate skill name: {name}")
        continue
      seen_skills.add(name)

      skills.append(Skill(name, description, root))
      skills_found += 1
  print(f"Found {skills_found} skills.")
  return skills


def download_github_repo(repo_url: str, output_dir: str, branch: str = "master"):
  """Downloads and extracts the GitHub repository zip file."""
  os.makedirs(output_dir, exist_ok=True)
  zip_url = f"{repo_url}/archive/refs/heads/{branch}.zip"
  print(f"Attempting to download repository zip via HTTP: {zip_url}...")

  with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip_file:
    zip_path = temp_zip_file.name

  try:
    request = urllib.request.Request(zip_url)
    with urllib.request.urlopen(request, timeout=30) as response:
      with open(zip_path, "wb") as out_file:
        shutil.copyfileobj(response, out_file)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
      zip_ref.extractall(output_dir)
    print(f"Repository extracted successfully from '{branch}' branch zip archive.")
  finally:
    if os.path.exists(zip_path):
      os.remove(zip_path)
      print(f"Deleted temporary zip file: {zip_path}")


def create_skill(client, skill: Skill):
  """Registers the skill via Vertex AI Skill Registry API."""
  name = skill.name
  description = skill.description
  skill_dir = skill.local_skill_dir
  print(f"Creating skill: {skill}")
  timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
  created_skill = client.skills.create(
      display_name=name,
      description=description,
      config={
          "local_path": skill_dir,
          "skill_id": f"{name}-{timestamp}"
      }
  )
  print(f"Created skill: {name}")
  return created_skill


def list_skills(client):
  """Lists all registered skills."""
  print("--- Registered Skills List ---")
  pager = client.skills.list()
  count = 0
  for skill in pager:
    print(f"Skill Name: {skill.name} | Display Name: {skill.display_name}")
    count += 1
  print(f"Total registered skills found: {count}")
  print("------------------------------")


def main():
  parser = argparse.ArgumentParser(description="Vertex AI Skill Registry Tool")
  parser.add_argument(
      "--project-id",
      default=os.environ.get("PROJECT_ID", "gcp-sandbox-kwlee"),
      help="Google Cloud Project ID"
  )
  parser.add_argument(
      "--location",
      default=os.environ.get("LOCATION", "us-central1"),
      help="Vertex AI location/region"
  )
  parser.add_argument(
      "--github-repo-url",
      default="https://github.com/kiwonilee/agentic-design-patterns-skills",
      help="GitHub Repository URL containing skills"
  )
  parser.add_argument(
      "--branch",
      default="master",
      help="GitHub repository branch to download"
  )
  parser.add_argument(
      "--skip-registration",
      action="store_true",
      help="Skip downloading and registering skills; just list existing skills"
  )

  args = parser.parse_args()

  print(f"Initializing Vertex AI client for project '{args.project_id}' in '{args.location}'...")
  vertexai.init(project=args.project_id, location=args.location)
  client = vertexai.Client(project=args.project_id, location=args.location)

  print("Listing existing skills before registration:")
  list_skills(client)

  if args.skip_registration:
    print("Skipping skill registration as requested.")
    return

  output_dir = tempfile.mkdtemp()
  try:
    download_github_repo(args.github_repo_url, output_dir, args.branch)
    skills = get_all_skills_from_dir(output_dir)
    for skill in skills:
      try:
        create_skill(client, skill)
      except Exception as e:
        print(f"Error registering skill '{skill.name}': {e}")
  finally:
    if os.path.exists(output_dir):
      shutil.rmtree(output_dir, ignore_errors=True)
      print(f"Cleaned up temporary directory: {output_dir}")

  print("\nListing registered skills after registration:")
  list_skills(client)


if __name__ == "__main__":
  main()
