import os
import vertexai

def search_skills_tool(query: str) -> dict:
    """Performs semantic RAG search on the registered playbook skills in the Vertex AI Agent Platform Skill Registry.
    
    Args:
        query: The search query string (e.g. 'GKE node upgrade' or 'logging troubleshooting').
        
    Returns:
        A dictionary containing the list of matching skills, with their display name, resource name, and description.
    """
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "gcp-sandbox-kwlee")
    location = os.environ.get("GCP_RESOURCES_LOCATION", "us-central1")
    
    # Initialize Vertex AI client
    client = vertexai.Client(project=project_id, location=location)
    
    try:
        response = client.skills.retrieve(
            query=query,
            config={"top_k": 3}
        )
        results = []
        for s in response.retrieved_skills:
            results.append({
                "skill_name": s.skill_name,
                "description": s.description,
            })
        return {"status": "success", "query": query, "skills": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}
