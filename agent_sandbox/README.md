# Agent Sandbox 의 격리된 코드 실행 환경을 연동하는 AI Agent

## 🚀 Agent Runtime 배포를 위한 기본 설정

### 1. 환경 변수 및 관련 API 활성화
배포에 사용할 Google Cloud Project ID를 설정하고 필수 API들을 활성화한 후, 배포 관련 환경 변수를 정의합니다.

```bash
cd ~/agent_platform/agent_sandbox
```

```bash
gcloud services enable \
    aiplatform.googleapis.com \
    logging.googleapis.com \
    cloudtrace.googleapis.com \
    storage.googleapis.com \
    iam.googleapis.com
```

```bash
export PROJECT_ID="YOUR_PROJECT_ID"

export STAGING_BUCKET_URI="gs://adk-${PROJECT_ID}"
export SERVICE_ACCOUNT="agent-sandbox-sa"
```

### 2. Cloud Storage 버킷 생성
배포 산출물을 저장할 Google Cloud Storage 버킷을 생성합니다. (이미 사용 중인 버킷이 있다면 이 단계는 건너뛰셔도 됩니다.)

```bash
gcloud storage buckets create ${STAGING_BUCKET_URI} --location=us-central1
```

### 3. 서비스 계정 생성 및 권한 설정
```bash
# 서비스 계정 이메일 주소 정의 (자동 매칭)
export SA_EMAIL="${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"

# 서비스 계정 생성
gcloud iam service-accounts create ${SERVICE_ACCOUNT} \
    --description="Service account for Agent Sandbox deployment" \
    --display-name="agent-sandbox-sa"

# 필요한 IAM 역할 목록
ROLES=(
    "roles/cloudtrace.user"
    "roles/cloudtrace.agent"
    "roles/logging.viewer"
    "roles/logging.logWriter"
    "roles/storage.objectAdmin"
    "roles/aiplatform.user"
)

# 반복문을 통해 권한 일괄 부여
for ROLE in "${ROLES[@]}"; do
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="${ROLE}"
done
```

### 4. `.env` 파일 생성 및 서비스 계정 추가
부모 디렉토리의 환경 변수 템플릿(`.env.template`)을 참조하여 프로젝트 정보를 치환한 로컬 `.env` 파일을 생성하고, 배포에 사용할 서비스 계정 이메일 변수를 안전하게 등록합니다.

```bash
# 1. 환경 변수 템플릿을 치환하여 로컬 .env 생성 (agent_sandbox 디렉토리 내부에서 실행)
sed -e "s|your-project-id|${PROJECT_ID}|g" \
    -e "s|your-gcs-bucket|${STAGING_BUCKET_URI}|g" \
    ../.env.template > .env

# 2. 서비스 계정 이메일을 배포 환경 변수로 추가 등록
echo "SERVICE_ACCOUNT=${SA_EMAIL}" >> .env

# 3. 최종 설정이 정상적으로 반영되었는지 확인
cat .env
```

#### 5. 코드 실행기(Code Executor) 구성 선택
현재 에이전트는 강력한 보안 격리와 아티팩트 보존이 지원되는 **Vertex AI 관리형 샌드박스(`AgentEngineSandboxCodeExecutor`)**를 메인 코드 실행 환경으로 고정하여 구성하고 있습니다.

* **격리된 보안 환경**: Google Cloud 내부의 전용 다중 레이어 격리 가상 환경에서 파이썬 코드가 컴파일 및 실행됩니다.
* **아티팩트 장기 저장**: 연산 수행 중 생성된 이미지 및 데이터 파일(CSV, JSON 등)이 설정된 Cloud Storage(GCS) 버킷에 자동 보존(최대 14일)됩니다.
* **상태 유지(Stateful)**: 대화 세션 내에서 생성된 변수 상태와 메모리가 유지되어 심층적인 데이터 연산이 가능합니다.

> [!NOTE]
> 만약 Sandbox API 사용에 제한이 있거나, 인프라 생성 절차 없이 가볍고 빠른 경량 데이터 연산기가 필요하다면 하단의 **`BuiltInCodeExecutor` 대체 구성 제안**을 참고하여 전환할 수 있습니다.

---

## 🚀 Agent Runtime 배포

아래의 명령어를 실행하여 에이전트를 Vertex AI Agent Runtime에 성공적으로 배포합니다.
```bash
uv run python agent_runtime.py
```
* **배포 작동 순서:**
  1. 최상위 `AgentEngine` 컨테이너 리소스를 선제 생성합니다.
  2. 생성된 부모 컨테이너 아래에 독립적인 관리형 Sandbox(`sandboxEnvironments`)를 동적으로 구성합니다.
  3. 생성된 Sandbox 리소스 명을 에이전트 배포 시 `SANDBOX_RESOURCE_NAME` 환경 변수로 주입합니다.

* **배포 성공 시 로그 예시:**
  ```text
  Initializing Vertex AI Client (Project: gcp-sandbox-kwlee, Location: us-central1)...
  Creating top-level AgentEngine container...
  ✅ Agent Runtime container created: projects/458778613248/locations/us-central1/reasoningEngines/4575110214373605376
  Creating Agent Sandbox under projects/458778613248/locations/us-central1/reasoningEngines/4575110214373605376...
  ✅ Sandbox created successfully! Resource name: projects/458778613248/locations/us-central1/reasoningEngines/4575110214373605376/sandboxEnvironments/3749626021297520640
  Injecting SANDBOX_RESOURCE_NAME into local environment: projects/458778613248/locations/us-central1/reasoningEngines/4575110214373605376/sandboxEnvironments/3749626021297520640
  Wrapping agent in AdkApp...
  Deploying Agent to Agent Runtime container...
  
  ✅ Deployment successful!
  Remote Agent Name: projects/458778613248/locations/us-central1/reasoningEngines/4575110214373605376
  ```

---

## 🔍 테스트

배포 완료 후 반환받은 `REASONING_ENGINE_ID`를 이용하여 에이전트와 대화를 시작하고 동작을 직접 검증합니다.

### 1. 세션 생성
새로운 세션을 생성하여 대화를 준비합니다.
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

### 2. 쿼리 실행 (대화 테스트)
세션 생성 성공 시 전달받은 `SESSION_ID`를 등록하여 샌드박스 내부에서 실제 코드 연산이 동반되는 질문을 에이전트에게 던져봅니다.
```bash
export SESSION_ID="[위 단계에서 발급받은 SESSION_ID]"

curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  https://us-central1-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}:streamQuery \
  -d '{
    "class_method": "async_stream_query",
    "input": {
      "user_id": "test_user",
      "session_id": "'"${SESSION_ID}"'",
      "message": "1부터 100까지의 숫자 중 소수(Prime Number)의 개수를 구하는 파이썬 코드를 작성하고 실행 결과를 알려줘."
    }
  }'
```

---

## 💡 대체 구성 제안: `BuiltInCodeExecutor` (경량 내장 실행기)

`BuiltInCodeExecutor`는 Gemini LLM 자체에 탑재된 코드 실행 확장 프로그램(Code Execution Extension)을 직접 제어하는 무설정(No-ops) 경량형 네이티브 도구입니다.

### 💻 코드 적용 가이드 (수동 전환 방법)

#### 1. `agent.py` 수정
기존의 `AgentEngineSandboxCodeExecutor` 대신 아래와 같이 내장 실행기로 정의합니다:
```python
import os
from google.adk.agents.llm_agent import Agent
from google.adk.code_executors.built_in_code_executor import BuiltInCodeExecutor

code_executor = BuiltInCodeExecutor()

data_analyst = Agent(
    model="gemini-3.5-flash",
    name="data_analyst",
    description="내장 코드 실행기를 활용하는 경량 데이터 분석가",
    instruction="""코드 실행기 도구를 사용하여 요청하신 연산을 수행하고 그 결과를 보고하세요.""",
    code_executor=code_executor,
    output_key="analysis_result"
)
```

#### 2. `agent_runtime.py` 수정
Sandbox 사전 생성 절차를 제거하고 가볍게 배포하도록 구성합니다:
```python
#!/usr/bin/env python3
import os
import vertexai
from vertexai.agent_engines import AdkApp

PROJECT_ID = "gcp-sandbox-kwlee"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://adk-sandbox-bucket"

client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

from agent import data_analyst as agent
adk_app = AdkApp(agent=agent)

remote_app = client.agent_engines.create(
    agent=adk_app,
    config={
        "display_name": "Agent BuiltIn-Executor",
        "requirements": [
            "google-adk",
            "google-cloud-aiplatform[adk,agent_engines]"
        ],
        "staging_bucket": STAGING_BUCKET,
        "extra_packages": ["agent.py"],
        "env_vars": {
            "GOOGLE_CLOUD_LOCATION": "global",
            "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
            "ADK_SESSION_SERVICE_URI": "agentengine://",
            "ADK_MEMORY_SERVICE_URI": "agentengine://",
            "ADK_ARTIFACT_SERVICE_URI": STAGING_BUCKET,
        }
    },
)

print(f"배포 완료! 원격 에이전트 ID: {remote_app.api_resource.name}")
```
