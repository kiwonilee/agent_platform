# ADK 코드 실행기 (Code Executor) 가이드 (#Agent Sandbox, #Code Execution, #Agent Runtime)

ADK(Agent Development Kit) 에이전트에서 데이터 분석이나 수치 연산을 위해 파이썬 코드를 작성하고 실행할 때 선택할 수 있는 **두 가지 코드 실행 방식(Code Execution Options)** 에 대한 비교 및 원격 배포·테스트 가이드입니다.

---

## ⚙️ 코드 실행 방식 개요

에이전트가 코드를 해석하고 실행하는 방법은 다음 두 가지로 분류되며, `agent.py`에서 환경 변수(`CODE_EXECUTOR_TYPE`)를 감지하여 동적으로 실행 방식을 변경할 수 있도록 유연하게 구현되었습니다:

1. **`BuiltInCodeExecutor` (추천 / 내장형)**: Gemini 모델 자체에 내장된 ADK 네이티브 코드 실행 도구(Gemini Code Execution Extension)를 활용하는 방식 (경량 및 무설정)
2. **`AgentEngineSandboxCodeExecutor` (관리형)**: Vertex AI의 관리형 격리 보안 샌드박스(`sandboxEnvironments`) 리소스를 생성하여 사용하는 방식

```python
# agent.py의 동적 실행기 선택 로직 (실제 기본값: SANDBOX)
executor_type = os.getenv("CODE_EXECUTOR_TYPE", "SANDBOX").upper()

if executor_type == "SANDBOX":
    sandbox_resource_name = os.getenv("SANDBOX_RESOURCE_NAME")
    code_executor = AgentEngineSandboxCodeExecutor(sandbox_resource_name=sandbox_resource_name)
else:
    code_executor = BuiltInCodeExecutor()

```

---

## 🔍 방식 1: `BuiltInCodeExecutor` (Gemini 내장 코드 실행기)

Gemini 모델의 Code Execution Extension(코드 실행 확장 프로그램)과 결합된 ADK 자체 네이티브 실행 기능입니다.

* **핵심 특징:**
  * ⚡ **빠르고 간단한 시작**: GCS 버킷이나 별도의 Vertex AI Sandbox 리소스를 사전에 생성/프로비저닝할 필요가 없습니다.
  * 🧩 **즉각적인 플러그 앤 플레이**: Gemini API 호출과 동시에 별도 설정 없이 바로 동작합니다.
  * 💡 **Gemini 최적화**: Gemini 모델의 컨텍스트 윈도우 내에서 네이티브하게 작동하여 지연 시간을 최소화합니다.
  * 🔄 **세션 내 임시 상태 유지**: 단일 채팅 세션의 대화 턴 내에서 상태 및 변수를 지속적으로 공유합니다.
* **적합한 사례**: 빠른 시연(Demo), 튜토리얼, 프로토타이핑 검증 작업이나 파일 저장 및 별도의 컴퓨팅 자원 튜닝이 필요하지 않는 AI 서비스 구현 시 매우 적합합니다.

### 💻 `BuiltInCodeExecutor` 코드 구현 예시
코드 내에서 `BuiltInCodeExecutor`를 단독 혹은 강제하여 에이전트를 설정하려면 아래와 같이 간결하게 구현할 수 있습니다:

```python
from google.adk.agents.llm_agent import Agent
from google.adk.code_executors.built_in_code_executor import BuiltInCodeExecutor

# 에이전트 내에 BuiltInCodeExecutor 직접 지정
data_analyst = Agent(
    model="gemini-3.5-flash",
    name="data_analyst",
    description="내장 코드 실행기를 활용하는 데이터 분석가 에이전트",
    instruction="""코드 실행기 도구를 사용하여 요청하신 연산을 수행하고 그 결과를 보고하세요.""",
    code_executor=BuiltInCodeExecutor(), # 내장 실행기 설정 (추가 설정 불필요)
    output_key="analysis_result"
)
```


---

## 🔍 방식 2: `AgentEngineSandboxCodeExecutor` (Vertex AI 관리형 샌드박스)

Vertex AI Agent Engine 내에 격리된 관리형 샌드박스 환경을 생성하고 이를 ADK 에이전트와 연결하여 사용합니다.

* **핵심 특징:**
  * 🔒 **격리된 보안 환경**: 엔터프라이즈 레벨의 다중 레이어 보안 격리 환경을 제공합니다.
  * 💾 **아티팩트 자동 저장**: 실행 중에 생성된 차트 이미지나 CSV 결과물 등이 Google Cloud Storage(GCS)에 자동으로 보관됩니다.
  * 🔄 **상태 보존(Stateful)**: 세션 내에서 정의한 변수나 데이터 상태가 최대 14일 동안 연속해서 보존됩니다.
  * ⚡ **컴퓨팅 사양 조정**: 샌드박스의 컴퓨팅 리소스(CPU, 메모리 등)를 자유롭게 변경하고 세밀하게 제어할 수 있습니다.
* **적합한 사례**: 강력한 보안 격리가 필요하고, 생성되는 파일 아티팩트를 장기 저장 및 연동해야 하며, 대규모 프로덕션 환경에 최적화된 에이전트 개발 시 적합합니다.

> [!WARNING]
> **Sandbox API 활성화 제한 주의**  
> 일부 GCP 프로젝트(예: `gcp-sandbox-kwlee`)나 계정 유형에 따라 Vertex AI 관리형 Sandbox API 엔드포인트(`sandboxEnvironments`)가 화이트리스트 처리되어 있지 않거나 비활성화되어 있는 경우, 샌드박스 생성 API 호출 시 `404 Not Found` 에러가 발생합니다.  
> 이 경우, **방식 1: `BuiltInCodeExecutor`**로 전환하여 서비스를 즉각 구현하고 원격 배포할 수 있습니다.

---

## 📊 두 방식 한눈에 비교하기

| 비교 항목 | `BuiltInCodeExecutor` (기본 추천) | `AgentEngineSandboxCodeExecutor` |
| :--- | :--- | :--- |
| **설정 복잡도** | 매우 쉬움 (별도 인프라 설정 없음) | 보통 (GCS 버킷 및 Agent Runtime 리소스 사전 생성 필요) |
| **지원 모델** | Gemini 모델 제품군 전용 (Gemini 2.0 이상) | 모든 대형 언어 모델 (Gemini, Claude 등 멀티 모델 지원) |
| **결과물 보존 (Artifacts)** | 인메모리 방식 (대화 세션 종료 시 소멸) | GCS 버킷에 자동 보존 (최대 14일 장기 저장) |
| **컴퓨팅 자원 제어** | 제공되는 사양으로 고정 | 사용자가 사양(CPU, RAM) 설정 가능 |
| **대화 상태 보존 (State)** | 단일 대화 세션의 연속 턴 동안 유지 | 세션별 최대 14일 동안 상태 및 변수 보존 |
| **최적 시나리오** | 빠른 시연, PoC, Gemini 전용 에이전트 개발 | 프로덕션 에이전트, 멀티 모델, 대용량 파일 아티팩트 보존 |

---

## 🚀 배포 가이드

원하시는 실행 방식에 맞게 배포 스크립트를 선택하여 실행할 수 있습니다.

### 💡 옵션 A: `BuiltInCodeExecutor` 기반 배포 (무설정 / 즉시 사용)
별도의 Sandbox 사전 생성 없이 즉시 모델 내장 도구로 코드를 실행하도록 에이전트를 배포합니다.

```bash
.venv/bin/python agent_runtime.py
```

* **배포 성공 로그 예시:**
  ```
  Initializing Vertex AI Client (Project: gcp-sandbox-kwlee, Location: us-central1)...
  Using BuiltInCodeExecutor (no managed sandbox pre-creation required)...
  Wrapping agent in AdkApp...

  ✅ Deployment successful!
  Remote Agent Name: projects/458778613248/locations/us-central1/reasoningEngines/5111522355146915840
  ```

---

### 💡 옵션 B: `AgentEngineSandboxCodeExecutor` 기반 배포 (Vertex AI 관리형 샌드박스)
독립적인 격리 샌드박스를 사전 생성하고, 이를 에이전트 환경 변수로 연결하여 배포합니다.

```bash
.venv/bin/python agent_runtime_sandbox.py
```

* **작동 프로세스:**
  1. 최상위 `AgentEngine` 컨테이너 리소스를 먼저 생성하여 고유의 API 식별 경로를 확보합니다.
  2. 생성된 컨테이너 리소스 명을 부모 경로로 설정하여 격리된 관리형 Sandbox(`sandboxEnvironments`)를 그 하위에 동적으로 생성합니다.
  3. 성공적으로 발급된 Sandbox Resource Name을 에이전트 배포 환경 변수(`SANDBOX_RESOURCE_NAME`)로 주입합니다.
  4. 에이전트 내 `CODE_EXECUTOR_TYPE`을 `"SANDBOX"`로 자동 구성하여 격리형 샌드박스 연동 모드로 에이전트를 배포합니다.

---

## 🔍 원격 API 테스트 및 검증

원격으로 배포된 에이전트와 대화 세션을 생성하고, 코드가 실행되는 질문에 대해 연산을 수행하는 API 호출 흐름입니다. (아래 예시는 성공적으로 배포 완료된 **옵션 A** 기준의 테스트 가이드입니다.)

### 1단계: 대화 세션 생성
원격 에이전트(`REASONING_ENGINE_ID`)로 새로운 고유 대화 세션 ID를 발급받습니다.

```bash
export REASONING_ENGINE_ID="5111522355146915840"
export PROJECT_NUMBER="458778613248"

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

**응답 성공 예시 (`output`)**
```json
{
  "output": {
    "user_id": "test_user",
    "app_name": "5111522355146915840",
    "id": "6427397049267781632",
    "last_update_time": 1781273030.168844,
    "events": [],
    "state": {}
  }
}
```

발급받은 세션 ID를 복사하여 환경 변수로 할당합니다:
```bash
export SESSION_ID="6427397049267781632"
```

### 2단계: 질문 던지기 (코드 연산 요청)
대화 세션 상에서 에이전트에게 수학 연산 및 파이썬 코드 실행이 동반되는 질문을 전송하고, 실시간 응답을 스트리밍(`streamQuery`)으로 가져옵니다.

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
      "message": "10의 9제곱에서 12의 5제곱을 뺀 값을 파이썬 코드로 계산해서 알려줘."
    }
  }'
```

**최종 연산 및 응답 결과 예시**
에이전트가 백엔드에서 자체적으로 파이썬 코드를 컴파일하고 완벽한 답변을 구성하여 스트림 결과를 반환합니다.

```json
{
  "model_version": "gemini-3.5-flash",
  "content": {
    "parts": [
      {
        "executable_code": {
          "code": "val_1 = 10 ** 9\nval_2 = 12 ** 5\nresult = val_1 - val_2\nprint(f'10^9 - 12^5 = {result:,}')\n",
          "language": "PYTHON"
        }
      },
      {
        "code_execution_result": {
          "outcome": "OUTCOME_OK",
          "output": "10^9 - 12^5 = 999,751,168\n"
        }
      },
      {
        "text": "$10^9$ (10의 9제곱)에서 $12^5$ (12의 5제곱)을 뺀 값은 **999,751,168**입니다."
      }
    ],
    "role": "model"
  }
}
```