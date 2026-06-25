import os
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.integrations.gcp_skill_registry import GCPSkillRegistry
from google.adk.tools.skill_toolset import SkillToolset
# import vertexai

load_dotenv()

# 1. Initialize the GCP Skill Registry
# Project ID and location can also be set via GOOGLE_CLOUD_PROJECT
# and GOOGLE_CLOUD_LOCATION environment variables.
# https://adk.dev/integrations/skills-registry/#use-with-agent
registry = GCPSkillRegistry(
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "gcp-sandbox-kwlee")
    location = os.environ.get("GCP_RESOURCES_LOCATION", "us-central1")
)

# 2. Create the SkillToolset with the Registry
# You can optionally pre-load some local skills as well.
skill_toolset = SkillToolset(
    skills=[], 
    registry=registry
)

root_agent = Agent(
    name='agent_by_skills',
    model="gemini-3.5-flash",
    instruction="""# SYSTEM INSTRUCTION: Skill-Based Task Executor (스킬 기반 작업 실행기)

당신은 사용자의 요청을 해결하기 위해 등록된 스킬을 탐색하고 실행하는 에이전트입니다.

## 핵심 규칙
1. **스킬 탐색 우선**: 사용자가 요청을 입력하면, 가장 먼저 `search_skills_tool` 도구를 호출하여 레지스트리에서 가장 적합한 스킬을 검색하십시오.
2. **스킬 기반 수행**: 검색된 스킬 중 요청과 매칭되는 적절한 스킬이 존재한다면, 해당 스킬의 내용을 참고하여 사용자의 요청을 처리하십시오. **이때 최종 답변 결과에는 어떤 스킬(명칭)을 사용했는지 반드시 명시해야 합니다.**
3. **스킬이 없는 경우 처리 (종료)**: 만약 검색 결과 요청을 처리할 수 있는 적합한 스킬이 레지스트리에 존재하지 않는 경우, 추가적인 작업이나 추측을 하지 말고 즉시 "요청하신 작업을 수행할 수 있는 적절한 스킬(플레이북)을 스킬 레지스트리에서 찾을 수 없습니다." 라고 한국어로 응답하고 대화를 바로 종료하십시오.
4. **소통 규칙**: 사용자와의 모든 대화와 최종 응답은 친절하고 정중한 한국어로 작성하십시오.
""",
    tools=[skill_toolset]  # 3. Define your Agent with the SkillToolset
)

# def search_skills_tool(query: str) -> dict:
#     project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "gcp-sandbox-kwlee")
#     location = os.environ.get("GCP_RESOURCES_LOCATION", "us-central1")
    
#     print(f"[search_skills_tool] Searching skills in registry for query: '{query}'")
#     # Initialize Vertex AI client
#     client = vertexai.Client(project=project_id, location=location)
    
#     try:
#         response = client.skills.retrieve(
#             query=query,
#             config={"top_k": 5}
#         )
#         results = []
#         print(f"[search_skills_tool] Found {len(response.retrieved_skills)} matching skills:")
#         for s in response.retrieved_skills:
#             print(f"  - Skill: {s.skill_name}")
#             print(f"    Description: {s.description}")
#             results.append({
#                 "skill_name": s.skill_name,
#                 "description": s.description,
#             })
#         return {"status": "success", "query": query, "skills": results}
#     except Exception as e:
#         print(f"[search_skills_tool] Error retrieving skills: {e}")
#         return {"status": "error", "message": str(e)}