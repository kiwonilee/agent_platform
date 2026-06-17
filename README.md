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

To run an agent, execute it from this root directory using `uv run` with the `--package` flag (Method A: Workspace Package Execution, recommended standard):

```bash
# Run agent registry (구 MCP 에이전트)
uv run --package agent-registry python agent_registry/agent_runtime.py

# Run skill registry
uv run --package skill-registry python skill_registry/agent_runtime.py

# Run agent runtime (날씨/시간 에이전트)
uv run --package agent-runtime python agent_runtime/agent_runtime.py

# Run agent sandbox
uv run --package agent-sandbox python agent_sandbox/agent_runtime.py
```

---

## 🏛️ UV Workspace (Monorepo) 구조 및 개발 가이드

본 리포지토리는 여러 개의 독립적인 Vertex AI ADK 에이전트를 효율적으로 공동 개발하기 위해 **UV Workspace (Monorepo)** 표준 모델을 채택하고 있습니다.

### 🌟 핵심 설계 특징
1. **단일 가상환경 통합 관리**: 루트 경로의 `.venv` 하나에서 하위 모든 에이전트의 라이브러리를 중앙 관리하여 중복 다운로드와 디스크 용량 낭비를 없앴습니다.
2. **Vertex AI (Python 3.11) 호환성 보장**: 클라우드 실행환경 버전에 일치하는 **CPython 3.11** 기반의 통합 `uv.lock` 파일을 유지하여 로컬과 클라우드 배포 간 라이브러리 충돌이 발생하지 않습니다.
3. **독립 패키지 정의**: 각 에이전트 디렉토리는 고유의 `pyproject.toml`을 가져 개별 패키지로서의 독립성을 완전히 유지합니다.

### 🛠️ 로컬 환경 초기화 (Environment Sync)
코드 수정 및 협업을 시작할 때, 루트 디렉토리에서 아래 단 한 줄의 명령어로 모든 패키지 종속성을 자동으로 빌드 및 정렬할 수 있습니다.
```bash
# 루트 디렉토리에서 최초 1회 실행
uv sync
```
이 명령어는 하위 모든 서브 디렉토리의 패키지 요구 명세를 읽어 단일 락 파일(`uv.lock`) 및 최적화된 `.venv` 가상환경을 알아서 완성해 줍니다.

---

## 🚀 개별 에이전트 수동/독립 배포 가이드

전체 배포 스크립트인 `run.sh`를 사용하지 않고, 수정한 **특정 에이전트 하나만 클라우드(Vertex AI)에 단독으로 배포**하고 싶을 때는 아래 가이드를 따릅니다.

### 1) 방법 A: 워크스페이스 루트에서 단독 배포 (가장 추천)
하위 폴더로 이동할 필요 없이, 최상위 루트 경로에서 특정 에이전트 패키지만 지정해 즉각 배포를 실행합니다.

```bash
# ① Agent Registry 단독 배포
uv run --package agent-registry python agent_registry/agent_runtime.py

# ② Agent Sandbox 단독 배포
uv run --package agent-sandbox python agent_sandbox/agent_runtime.py

# ③ Skill Registry 단독 배포
uv run --package skill-registry python skill_registry/agent_runtime.py

# ④ Agent Runtime 단독 배포
uv run --package agent-runtime python agent_runtime/agent_runtime.py
```

### 2) 방법 B: 서브 디렉토리로 이동하여 단독 배포
원하는 에이전트의 개발 작업 폴더로 직접 진입하여 배포 스크립트를 기동합니다. 이동하더라도 새로 가상환경을 만들지 않고 자동으로 워크스페이스의 통합 `.venv`를 공유하므로 매우 빠르고 안전합니다.

```bash
# 원하는 에이전트 폴더로 이동
cd skill_registry

# 배포 스크립트 단독 기동
uv run python agent_runtime.py
```