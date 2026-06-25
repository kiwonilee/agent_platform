import os
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.integrations.skill_registry import GCPSkillRegistry
from google.adk.tools.skill_toolset import SkillToolset
# import vertexai

load_dotenv()

# 1. Initialize the GCP Skill Registry
# Project ID and location can also be set via GOOGLE_CLOUD_PROJECT
# and GOOGLE_CLOUD_LOCATION environment variables.
# https://adk.dev/integrations/skills-registry/#use-with-agent
registry = GCPSkillRegistry(
    project_id=os.environ.get("GOOGLE_CLOUD_PROJECT", "gcp-sandbox-kwlee"),
    location=os.environ.get("GCP_RESOURCES_LOCATION", "us-central1"),
)

# 2. Create the SkillToolset with the Registry
# You can optionally pre-load some local skills as well.
skill_toolset = SkillToolset(skills=[], registry=registry)

root_agent = Agent(
    name="agent_by_skills",
    model="gemini-3.5-flash",
    instruction="""
        당신은 사용자의 요청을 해결하기 위해 **Skill Registry**에 등록된 스킬을 탐색하고 실행하는 전문 AI 에이전트입니다.

        ## 핵심 수행 규칙

        1. **스킬 탐색 우선**
           - 사용자의 요청을 받으면 가장 먼저 `skill_toolset` 도구를 사용하여 Skill Registry에서 가장 적합한 스킬을 검색하십시오.

        2. **스킬 기반 수행 및 출처 명시**
           - 검색된 스킬 중 적절한 항목이 있다면, 해당 스킬의 내용을 철저히 참고하여 요청을 처리하십시오.
           - ⚠️ **필수**: 최종 답변에는 **어떤 스킬(명칭)을 사용했는지** 반드시 명확하게 밝혀야 합니다.

        3. **스킬 부재 시 예외 처리 (즉시 종료)**
           - 검색 결과 적합한 스킬이 없다면 임의로 추측하거나 추가 작업을 진행하지 마십시오.
           - 즉시 "요청하신 작업을 수행할 수 있는 적절한 스킬(플레이북)을 스킬 레지스트리에서 찾을 수 없습니다."라고 한국어로 응답하고 대화를 바로 종료하십시오.

        4. **소통 가이드라인**
           - 사용자와의 모든 대화 및 최종 응답은 친절하고 정중한 한국어로 작성하십시오.        
        """,
    # 3. Define your Agent with the SkillToolset/
    tools=[skill_toolset],
)
