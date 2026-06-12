# ADK 코드 실행기 (Code Executor) 가이드 (#Agent Sandbox, #Code Execution, #Agent Runtime)

ADK(Agent Development Kit) 에이전트에서 데이터 분석이나 수치 연산을 위해 파이썬 코드를 작성하고 실행할 때 선택할 수 있는 **두 가지 코드 실행 방식(Code Execution Options)** 에 대한 비교 및 원격 배포·테스트 가이드입니다.

---

## ⚙️ 코드 실행 방식 개요

에이전트가 코드를 해석하고 실행하는 방법은 다음 두 가지로 분류됩니다:
1. **`AgentEngineSandboxCodeExecutor`**: Vertex AI의 관리형 격리 보안 샌드박스를 활용하는 방식
2. **`BuiltInCodeExecutor`**: Gemini 모델 자체에 내장된 ADK 네이티브 코드 실행 도구를 활용하는 방식 (경량 및 통합형)

---

## 🔍 방식 1: `AgentEngineSandboxCodeExecutor` (Vertex AI 관리형 샌드박스)

Vertex AI Agent Engine 내에 격리된 관리형 샌드박스 환경을 생성하고 이를 ADK 에이전트와 연결하여 사용합니다.

* **핵심 특징:**
  * 🔒 **격리된 보안 환경**: 엔터프라이즈 레벨의 다중 레이어 보안 격리 환경을 제공합니다.
  * 💾 **아티팩트 자동 저장**: 실행 중에 생성된 차트 이미지나 CSV 결과물 등이 Google Cloud Storage(GCS)에 자동으로 보관됩니다.
  * 🔄 **상태 보존(Stateful)**: 세션 내에서 정의한 변수나 데이터 상태가 최대 14일 동안 연속해서 보존됩니다.
  * ⚡ **컴퓨팅 사양 조정**: 샌드박스의 컴퓨팅 리소스(CPU, 메모리 등)를 자유롭게 변경하고 세밀하게 제어할 수 있습니다.
* **적합한 사례**: 강력한 보안 격리가 필요하고, 생성되는 파일 아티팩트를 장기 저장 및 연동해야 하며, 대규모 프로덕션 환경에 최적화된 에이전트 개발 시 적합합니다.

---

## 🔍 방식 2: `BuiltInCodeExecutor` (Gemini 내장 코드 실행기)

Gemini 모델의 Code Execution Extension(코드 실행 확장 프로그램)과 결합된 ADK 자체 네이티브 실행 기능입니다.

* **핵심 특징:**
  * ⚡ **빠르고 간단한 시작**: 별도의 GCS 버킷이나 Vertex AI 샌드박스 리소스를 사전에 프로비저닝할 필요가 없습니다.
  * 🧩 **즉각적인 플러그 앤 플레이**: Gemini API 호출과 동시에 별도 설정 없이 바로 동작합니다.
  * 💡 **Gemini 최적화**: Gemini 모델의 컨텍스트 윈도우 내에서 네이티브하게 작동하여 지연 시간을 최소화합니다.
  * 🔄 **세션 내 임시 상태 유지**: 단일 채팅 세션의 대화 턴 내에서 상태 및 변수를 지속적으로 공유합니다.
* **적합한 사례**: 빠른 시연(Demo), 튜토리얼, 프로토타이핑 검증 작업이나 파일 저장 및 별도의 자원 튜닝이 필요하지 않는 경량 AI 서비스 구현 시 매우 적합합니다.

---

## 📊 두 방식 한눈에 비교하기

| 비교 항목 | `AgentEngineSandboxCodeExecutor` | `BuiltInCodeExecutor` |
| :--- | :--- | :--- |
| **설정 복잡도** | 보통 (GCS 버킷 및 Agent Runtime 리소스 사전 생성 필요) | 매우 쉬움 (별도 인프라 설정 없음) |
| **지원 모델** | 모든 대형 언어 모델 (Gemini, Claude 등 멀티 모델 지원) | Gemini 모델 제품군 전용 |
| **결과물 보존 (Artifacts)** | GCS 버킷에 자동 보존 (최대 14일 장기 저장) | 인메모리 방식 (대화 세션 종료 시 소멸) |
| **컴퓨팅 자원 제어** | 사용자가 사양(CPU, RAM) 설정 가능 | 제공되는 사양으로 고정 |
| **대화 상태 보존 (State)** | 세션별 최대 14일 동안 상태 및 변수 보존 | 단일 대화 세션의 연속 턴 동안 유지 |
| **개발 성숙도** | ✅ 엔터프라이즈 프로덕션 권장 | ⚠️ 빠른 프로토타이핑 및 데모 용도 |
| **최적 시나리오** | 프로덕션 에이전트, 멀티 모델, 파일 저장이 필요할 때 | 빠른 시연, PoC, Gemini 전용 에이전트 |

---

## 🚀 배포 가이드 (`AgentEngineSandboxCodeExecutor` 기반)

`agent_sandbox/agent_runtime.py` 스크립트를 실행하여 샌드박스를 우선 독립 생성하고, 에이전트 로직을 원격 런타임에 단일 스텝으로 배포합니다:

```bash
uv run python agent_runtime.py
```

* 배포가 완료되면 콘솔 창에 **Sandbox Resource Name**과 최종 **Remote Agent Name** 정보가 출력됩니다.

---

## 🔍 테스트

### 1단계: 최초 1회 대화 세션 생성
```bash
export REASONING_ENGINE_ID="5761272154511376384"
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
    "app_name": "5761272154511376384",
    "id": "5918349553886560256",
    "user_id": "test_user"
  }
}
```

발급받은 `"id"` 값을 복사하여 환경 변수로 할당합니다:
```bash
export SESSION_ID="5918349553886560256"
```

### 2단계: 첫 번째 질문 던지기 (샌드박스 연산 요청)
```bash
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  https://us-central1-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}:streamQuery \
  -d '{
    "class_method": "async_stream_query",
    "input": {
      "user_id": "test_user",
      "session_id": "${SESSION_ID}",
      "message": "10의 9제곱에서 12의 5제곱을 뺀 값을 파이썬 코드로 계산해서 알려줘."
    }
  }'
```