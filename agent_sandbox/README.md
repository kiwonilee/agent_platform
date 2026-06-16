# ADK 코드 실행기 (Code Execution in Agent Sandbox)

본 가이드는 ADK(Agent Development Kit) 에이전트가 데이터 가공, 수치 연산, 비즈니스 지표 산출 등을 수행할 때 사용하는 코드 실행 환경에 대한 설명 및 배포 안내서입니다.

현재 에이전트의 메인 코드베이스는 강력한 보안 격리와 아티팩트 보존이 지원되는 **Vertex AI 관리형 샌드박스(`AgentEngineSandboxCodeExecutor`)**만을 사용하도록 고정되어 구성되어 있습니다.

Gemini 모델 자체의 내장 기능을 사용하는 **`BuiltInCodeExecutor`** 방식은 로컬 테스트나 인프라 간소화가 필요한 경우에 활용할 수 있도록 **가이드 문서 전용(README.md)**으로 아래에 대체 구성안을 수록하였습니다.

---

## 🔒 기본 구성: `AgentEngineSandboxCodeExecutor` (Vertex AI 관리형 샌드박스)

현재 `agent.py` 및 `agent_runtime.py`에 기본 탑재된 프로덕션 지향 코드 실행기입니다.

### 🌟 핵심 특징
* **격리된 보안 환경**: Google Cloud 내부의 전용 다중 레이어 격리 가상 환경에서 파이썬 코드가 컴파일 및 실행됩니다.
* **아티팩트 장기 저장**: 연산 수행 중 생성된 이미지(예: matplotlib 시각화 차트) 및 데이터 파일(CSV, JSON 등)이 설정된 Cloud Storage(GCS) 버킷에 자동 보존(최대 14일)되어 추후 다운로드 및 API 연동이 용이합니다.
* **상태 유지(Stateful)**: 대화 세션 내에서 생성된 변수 상태와 메모리 상태가 최대 14일 동안 연속해서 유지되므로 심층적인 데이터 탐색이 가능합니다.
* **컴퓨팅 사양 조정**: CPU 및 메모리 자원 크기를 목적에 맞게 자유롭게 튜닝할 수 있습니다.

### ⚙️ 배포 및 실행 방법

1. **에이전트 런타임 배포**:
   아래 명령어를 통해 Vertex AI Agent Engine 상에 격리형 샌드박스 환경을 자동으로 생성하고 에이전트를 빌드 및 배포합니다.
   ```bash
   .venv/bin/python agent_runtime.py
   ```
   * **배포 작동 순서:**
     1. 최상위 `AgentEngine` 컨테이너 리소스를 선제 생성합니다.
     2. 생성된 부모 컨테이너 아래에 독립적인 관리형 Sandbox(`sandboxEnvironments`)를 동적으로 구성합니다.
     3. 생성된 Sandbox 리소스 명을 에이전트 배포 시 `SANDBOX_RESOURCE_NAME` 환경 변수로 주입합니다.

   > [!NOTE]
   > 별도의 Service Account나 Agent Identity(예: `types.IdentityType.AGENT_IDENTITY`)를 에이전트 설정(`config`)에 지정하지 않는 경우, 에이전트 구동용 기본 신원으로서 `sa://service-PROJECT_NUMBER@gcp-sa-aiplatform-re.iam.gserviceaccount.com` 형식의 서비스 어카운트가 자동으로 할당 및 사용됩니다. (이 정보는 API 응답의 `effective_identity` 값으로 확인할 수 있습니다.)

2. **배포 성공 시 로그 예시:**
   ```
   Initializing Vertex AI Client (Project: gcp-sandbox-kwlee, Location: us-central1)...
   Creating top-level AgentEngine container...
   ✅ AgentEngine container created: projects/458778613248/locations/us-central1/agentEngines/4389363118023639040
   Creating Agent Sandbox under projects/458778613248/locations/us-central1/agentEngines/4389363118023639040...
   ✅ Sandbox created successfully! Resource name: projects/458778613248/locations/us-central1/sandboxes/4389363118023639040
   Wrapping agent in AdkApp...
   Deploying Agent to Vertex AI Agent Runtime...
   
   ✅ Deployment successful!
   Remote Agent Name: projects/458778613248/locations/us-central1/reasoningEngines/4389363118023639040
   ```

---

## 💡 대체 구성 제안 (README 전용 가이드): `BuiltInCodeExecutor`

> [!NOTE]
> 만약 Vertex AI 샌드박스 API 권한(Quota/White-listing) 제한으로 인해 `AgentEngine container` 또는 `Sandbox` 생성 중 에러가 발생하거나, 인프라 생성 절차 없이 가볍고 저렴하게 에이전트를 구동하고 싶다면 아래의 `BuiltInCodeExecutor` 방식으로 코드를 대체 적용할 수 있습니다.

`BuiltInCodeExecutor`는 Gemini LLM 자체 내장된 코드 실행 확장 프로그램(Code Execution Extension)을 직접 제어하는 경량형 네이티브 도구입니다.

### 🌟 핵심 특징
* ⚡ **초간단 시작**: Cloud Storage 버킷 연결이나 Vertex AI Sandbox 리소스를 만들 필요가 전혀 없습니다.
* 🧩 **무설정(No-ops)**: Gemini API가 활성화되어 있다면 추가 과금이나 전용 노드 프로비저닝 없이 즉시 컴파일러가 작동합니다.
* 🚀 **컨텍스트 최적화**: 모델의 추론 과정 내에서 가볍게 처리되므로 동적 API 연산의 레이턴시(지연 시간)가 단축됩니다.

### 💻 코드 적용 가이드 (수동 전환 방법)

코드를 내장 코드 실행기 방식으로 수동 전환하려면 다음의 간단한 수정 작업만 수행하시면 됩니다.

#### 1. `agent.py` 수정
기존의 `AgentEngineSandboxCodeExecutor` 임포트와 구성을 제거하고, 아래와 같이 내장 실행기로 정의합니다:

```python
import os
from google.adk.agents.llm_agent import Agent
# 내장 실행기 임포트
from google.adk.code_executors.built_in_code_executor import BuiltInCodeExecutor

# 별도 설정 없이 바로 인스턴스화
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
인프라(Sandbox) 사전 생성 로직을 걷어내고, Agent Runtime에 에이전트를 즉각 원격 등록하도록 구성합니다:

```python
#!/usr/bin/env python3
import os
import vertexai
from vertexai.agent_engines import AdkApp

PROJECT_ID = "gcp-sandbox-kwlee"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://adk-sandbox-bucket"

# Vertex Client 초기화
client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

# 에이전트 가져오기
from agent import data_analyst as agent
adk_app = AdkApp(agent=agent)

# 원격 Agent Runtime에 배포 (샌드박스 환경 변수 불필요)
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

---

## 📊 실행 방식별 핵심 비교 요약

| 비교 항목 | `AgentEngineSandboxCodeExecutor` (실제 코드 구성) | `BuiltInCodeExecutor` (README 가이드 대체안) |
| :--- | :--- | :--- |
| **적용 시점** | 엔터프라이즈 프로덕션 환경, 보안 격리 및 결과 보존 필수 시 | 빠른 검증(PoC), 데모 빌드, API 권한 획득 지연 시 |
| **GCS 인프라 필요성** | 필수 (아티팩트 및 임시 세션 파일 영구 기록) | 불필요 (순수 텍스트 컨텍스트 기반 연산) |
| **컴퓨팅 하드웨어 변경**| vCPU, RAM 등 기호에 부합하는 리소스 세부 튜닝 가능 | 기본 사양으로 고정 제공 |
| **추론 속도** | 샌드박스 부팅 및 입출력 세션 제어로 수 초 추가 지연 발생 가능 | 모델의 자체 확장을 타므로 지연 시간 최소화 |

---

## 🔍 테스트

### 1단계: 최초 1회 대화 세션 생성
```bash
export REASONING_ENGINE_ID="[배포 완료 후 발급받은 REASONING_ENGINE_ID]"
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

### 2단계: 첫 번째 질문 던지기 (샌드박스 내 코드 실행 기능 테스트)
```bash
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