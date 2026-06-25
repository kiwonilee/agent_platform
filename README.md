# Agent Platform

Vertex AI Agent Engine에 다중 AI 에이전트를 통합 배포하고 관리하기 위한 **UV Workspace (Monorepo)** 기반의 표준 저장소입니다.

---

## 🏛️ 1. 아키텍처 및 UV Workspace 구조

본 프로젝트는 여러 개의 독립적인 Vertex AI ADK 에이전트를 일관되게 개발하고 배포하기 위해 **UV Workspace** 단일 가상환경 모델을 채택하고 있습니다.

### 📦 구성 에이전트 패키지
1. **[`agent_registry`](agent_registry/README.md)** (`agent-registry`): MCP(Model Context Protocol) 툴셋을 이용해 Enterprise BigQuery 데이터셋을 쿼리하고 데이터 분석 결과를 요약하는 에이전트입니다.
2. **[`agent_sandbox`](agent_sandbox/README.md)** (`agent-sandbox`): 코드를 격리된 환경에서 안전하게 실행할 수 있도록 돕는 샌드박스 에이전트입니다.
3. **[`skill_registry`](skill_registry/README.md)** (`skill-registry`): 도구 및 스킬 등록부를 관리하는 에이전트입니다.
4. **[`agent_runtime`](agent_runtime/README.md)** (`agent-runtime`): 날씨, 시간 등 공통 시스템 도구를 탑재한 날씨/시간 실행 에이전트입니다.

> **참고**: 각 에이전트별 특화된 배포 방법 및 요구되는 IAM 권한 설정, 구체적인 테스트 방법은 위 각 폴더의 `README.md`에 자세히 안내되어 있습니다.

### 🌟 Workspace 주요 특징
* **단일 가상환경 통합 (`.venv`)**: 개별 프로젝트마다 가상환경을 복제 생성할 필요 없이, 루트 경로의 `.venv` 하나를 하위 4개 에이전트가 완벽히 공유하여 디스크 및 다운로드 용량을 최소화합니다.
* **Vertex AI(Python 3.11) 호환성 잠금**: 구글 클라우드 Agent Runtime 실행환경 버전에 완벽히 부합하도록 모든 패키지의 요구 버전을 `Requires-Python = ">=3.11, <3.12"`(CPython 3.11.x)로 일치시켰으며, 이를 `uv.lock`으로 묶어 패키지 충돌을 원천 차단합니다.
* **개별 패키지 독립성**: 각 폴더의 `pyproject.toml`은 에이전트 고유의 명세와 디펜던시를 명확하게 보존합니다.

---

## 🛠️ 2. 로컬 개발 환경 초기화 (Sync)

협업을 시작하거나 코드를 로컬 가상환경에 동기화할 때, 워크스페이스 최상위 루트 디렉토리에서 아래 단 한 줄의 명령어로 모든 패키지 종속성을 정렬할 수 있습니다.

```bash
# 최상위 루트 경로에서 실행 (로컬 가상환경 빌드 및 동기화)
uv sync
```
이 명령어는 하위 모든 패키지의 요구 명세를 자동으로 결합하여 단일 락 파일(`uv.lock`) 및 최적화된 최신 가상환경 `.venv`를 구축합니다.

> [!IMPORTANT]
> **`google-adk` 버전 준수 사항 (필수):**
> 에이전트 배포 중 `TypeError: cannot pickle '_thread.lock' object` 오류가 발생하는 것을 방지하기 위해 **`google-adk>=2.2.0`** 버전 사용이 강제됩니다.
> 
> * **예방법:** 다른 장비에서 새로 개발 환경을 구축할 때는 수동 설치(`pip install` 등) 대신 반드시 최상위 디렉토리에서 `uv sync`를 실행하여 락 파일(`uv.lock`)에 지정된 최신 가상환경을 동기화해야 합니다.
> * **프로그램 레벨 통제:** 워크스페이스 내 모든 `pyproject.toml` 및 배포 스크립트에서도 `google-adk>=2.2.0`으로 강제하도록 종속성이 수정되어 있습니다.

---

## 🔑 3. 환경 변수 설정 (Environment Configuration)

각 에이전트가 Vertex AI 및 Google Cloud 리소스에 접근하기 위해 프로젝트 ID(`PROJECT_ID`) 및 GCS 버킷 주소(`STAGING_BUCKET_URI`) 등의 환경변수 설정이 필요합니다.

### 자동 배포 스크립트를 사용할 경우
배포 스크립트(`run.sh`)가 실행 과정에서 루트 경로에 `.env` 파일이 없을 경우 `.env.template`을 기반으로 설정을 안내하며, 생성 완료 시 하위 패키지 디렉토리에 자동으로 전파 및 배포를 완료합니다.

### 수동으로 설정할 경우
1. 최상위 디렉토리에서 아래 명령어로 템플릿 파일로부터 `.env`를 생성하고 사용자의 Google Cloud 프로젝트 ID 및 버킷 이름으로 교체합니다.
   ```bash
   # 1. 환경 변수 정의 (자신의 프로젝트 ID와 GCS 버킷 이름 지정)
   export PROJECT_ID="YOUR_PROJECT_ID"
   export STAGING_BUCKET_URI="gs://YOUR_STAGING_BUCKET_URI"

   # 2. 치환 스크립트 실행 (환경 변수가 자동으로 주입됩니다)
   sed -e "s|your-project-id|${PROJECT_ID}|g" \
       -e "s|your-gcs-bucket|${STAGING_BUCKET_URI}|g" \
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

## 🚀 4. 에이전트 클라우드 배포 가이드 (Agent Runtime)

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

---

## 🔍 5. 공통 API 호출 테스트 가이드

배포된 Reasoning Engine(Agent Runtime)에 API 요청을 보내 테스트를 수행합니다.

### 💡 자동화 테스트 스크립트 사용 (`test.sh`)
이 과정을 편리하게 실행할 수 있도록 `test.sh` 스크립트를 제공합니다.

배포 스크립트(`run.sh`) 실행이 완료되면, 터미널 맨 하단에 배포된 모든 에이전트들의 고유 ID가 `export` 명령어 형태로 일괄 출력됩니다. 해당 출력 블록을 복사해 터미널 세션에 입력(등록)하여 사용합니다.

#### 방법 1: 전체 에이전트 일괄 테스트 (추천)
출력된 환경변수를 등록한 후 바로 아래 명령어를 실행하면, 자동으로 전체 통합 테스트를 순차 수행합니다:
```bash
chmod +x test.sh
./test.sh
```

#### 방법 2: 특정 에이전트 개별 테스트
환경변수로 내보낸 정보를 활용하거나, 혹은 직접 `REASONING_ENGINE_ID`를 매개변수로 명시하여 테스트할 수 있습니다.
```bash
# 등록한 특정 에이전트 테스트 (예: agent_runtime)
./test.sh agent_runtime

# 특정 ID를 직접 지정하여 테스트
./test.sh <REASONING_ENGINE_ID> [agent_registry|agent_sandbox|skill_registry|agent_runtime]
```

---

### 수동 테스트 (curl)

#### 1단계: 최초 1회 대화 세션 생성
```bash
export REASONING_ENGINE_ID="[배포 후 발급받은 REASONING_ENGINE_ID]"
export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")

curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  https://us-central1-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}:query \
  -d '{
    "class_method": "create_session",
    "input": {
      "user_id": "test_user"
    }
  }'
```

**출력 예시 (`output`)**
```json
{
  "output": {
    "last_update_time": 1781269005.17933,
    "events": [],
    "state": {},
    "app_name": "projects/...",
    "id": "5918349553886560256",
    "user_id": "test_user"
  }
}
```

발급받은 `"id"` 값을 복사하여 환경 변수로 할당합니다:
```bash
export SESSION_ID="5918349553886560256"
```

### 2단계: 질문 던지기 (메시지 스트리밍 쿼리)
```bash
# 각 에이전트별 테스트용 샘플 메시지 (선택하여 MESSAGE 변수에 지정 가능)
# - agent-registry: "현재 빅쿼리의 dataset 리스트 알려줘."
# - agent-sandbox: "1부터 100까지의 소수(Prime numbers)를 구하는 파이썬 코드를 작성하고 실행 결과를 알려줘."
# - skill-registry: "GKE 의 Cluster Upgrade 에 대한 Best Practice 에 대해서 알려줘"
# - agent-runtime: "뉴욕의 현재 날씨와 현재 시간을 알려줘."
export MESSAGE="뉴욕의 현재 날씨와 현재 시간을 알려줘."

curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  https://us-central1-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}:streamQuery \
  -d '{
    "class_method": "async_stream_query",
    "input": {
      "user_id": "test_user",
      "session_id": "'"${SESSION_ID}"'",
      "message": "'"${MESSAGE}"'"
    }
  }'
```
```