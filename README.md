# Agent Platform

Vertex AI Agent Engine에 다중 AI 에이전트를 통합 배포하고 관리하기 위한 **UV Workspace (Monorepo)** 기반의 표준 저장소입니다.

---

## 🏛️ 1. 아키텍처 및 UV Workspace 구조

본 프로젝트는 여러 개의 독립적인 Vertex AI ADK 에이전트를 일관되게 개발하고 배포하기 위해 **UV Workspace** 단일 가상환경 모델을 채택하고 있습니다.

### 📦 구성 에이전트 패키지
1. **`agent_registry`** (`agent-registry`): MCP(Model Context Protocol) 툴셋을 이용해 Enterprise BigQuery 데이터셋을 쿼리하고 데이터 분석 결과를 요약하는 에이전트입니다.
2. **`agent_sandbox`** (`agent-sandbox`): 코드를 격리된 환경에서 안전하게 실행할 수 있도록 돕는 샌드박스 에이전트입니다.
3. **`skill_registry`** (`skill-registry`): 도구 및 스킬 등록부를 관리하는 에이전트입니다.
4. **`agent_runtime`** (`agent-runtime`): 날씨, 시간 등 공통 시스템 도구를 탑재한 날씨/시간 실행 에이전트입니다.

### 🌟 Workspace 주요 특징
* **단일 가상환경 통합 (`.venv`)**: 개별 프로젝트마다 가상환경을 복제 생성할 필요 없이, 루트 경로의 `.venv` 하나를 하위 4개 에이전트가 완벽히 공유하여 디스크 및 다운로드 용량을 최소화합니다.
* **Vertex AI(Python 3.11) 호환성 잠금**: 구글 클라우드 Vertex AI Reasoning Engine 실행환경 버전에 완벽히 부합하도록 모든 패키지의 요구 버전을 `Requires-Python = ">=3.11, <3.12"`(CPython 3.11.x)로 일치시켰으며, 이를 `uv.lock`으로 묶어 패키지 충돌을 원천 차단합니다.
* **개별 패키지 독립성**: 각 폴더의 `pyproject.toml`은 에이전트 고유의 명세와 디펜던시를 명확하게 보존합니다.

---

## 🛠️ 2. 로컬 개발 환경 초기화 (Sync)

협업을 시작하거나 코드를 로컬 가상환경에 동기화할 때, 워크스페이스 최상위 루트 디렉토리에서 아래 단 한 줄의 명령어로 모든 패키지 종속성을 정렬할 수 있습니다.

```bash
# 최상위 루트 경로에서 실행 (로컬 가상환경 빌드 및 동기화)
uv sync
```
이 명령어는 하위 모든 패키지의 요구 명세를 자동으로 결합하여 단일 락 파일(`uv.lock`) 및 최적화된 최신 가상환경 `.venv`를 구축합니다.

---

## 🔑 3. 환경 변수 설정 (Environment Configuration)

각 에이전트가 Vertex AI 및 Google Cloud 리소스에 접근하기 위해 프로젝트 ID(`PROJECT_ID`) 및 GCS 버킷 주소(`STAGING_BUCKET_URI`) 등의 환경변수 설정이 필요합니다.

### 자동 배포 스크립트를 사용할 경우
배포 스크립트(`run.sh`)가 실행 과정에서 루트 경로에 `.env` 파일이 없을 경우 `.env.template`을 기반으로 설정을 안내하며, 생성 완료 시 하위 패키지 디렉토리에 자동으로 전파 및 배포를 완료합니다.

### 수동으로 설정할 경우
1. 최상위 디렉토리에서 아래 명령어로 템플릿 파일로부터 `.env`를 생성하고 사용자의 Google Cloud 프로젝트 ID 및 버킷 이름으로 교체합니다.
   ```bash
   sed -e "s|\${PROJECT_ID}|YOUR_PROJECT_ID|g" \
       -e "s|\${STAGING_BUCKET_URI}|YOUR_STAGING_BUCKET_URI|g" \
       .env.template > .env
   ```
2. 생성된 `.env` 파일을 각 에이전트 디렉토리로 직접 복사 전파합니다.
   ```bash
   cp .env agent_registry/.env
   cp .env agent_sandbox/.env
   cp .env skill_registry/.env
   cp .env agent_runtime/.env
   ```

---

## 🚀 4. 에이전트 클라우드 배포 가이드 (Vertex AI)

작성 및 테스트가 완료된 에이전트 애플리케이션을 구글 클라우드 Vertex AI Reasoning Engine(Agent Runtime)에 배포하는 방식은 두 가지가 있습니다.

### 방법 A: 전체 에이전트 자동 배포 및 권한 위임 (`run.sh` 사용)
이 방식은 4개의 모든 에이전트를 순차적으로 배포하고, 배포 후 생성된 각각의 **Agent Identity**를 파싱하여 필요한 구글 클라우드 IAM 권한(`roles/aiplatform.user`, `roles/storage.objectAdmin`, `roles/bigquery.dataViewer` 등)을 자동으로 매핑 및 바인딩해 줍니다. 가장 편리하고 권장되는 프로덕션 배포 방식입니다.

```bash
# 전체 에이전트 배포 및 IAM 바인딩 자동 일괄 처리
bash run.sh
```

---

### 방법 B: 특정 에이전트 단독 배포 (수동)
특정 에이전트 폴더의 코드만 수정하여 **하나만 단독으로 클라우드에 배포**하고 싶을 때 사용합니다.

#### **1) 워크스페이스 최상위 루트 디렉토리에서 실행 (권장)**
하위 디렉토리로 이동할 필요 없이, 최상위 루트 경로에서 `--package` 플래그로 타겟 패키지를 지정하여 즉각 배포를 트리거합니다.

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

#### **2) 서브 패키지 디렉토리 내부에서 직접 실행**
원하는 에이전트 폴더에 들어간 뒤 `uv run`으로 배포를 기동합니다. 폴더 내부로 진입하더라도 새로 가상환경을 구축하지 않고 최상위 루트의 단일 `.venv` 가상환경을 공유하여 기동 속도가 매우 빠르고 종속성 충돌이 일어나지 않습니다.

```bash
# 원하는 폴더로 진입
cd agent_registry

# 개별 단독 배포
uv run python agent_runtime.py
```