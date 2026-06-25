# Agent Registry MCP 연동 (#Agent Identity, #Agent Registry, #MCP, #Agent Runtime)

이 프로젝트는 **GCP Agent Registry**에 등록된 **MCP(Model Context Protocol)** 도구 세트를 원격 **Agent Runtime**과 Agent Identity (`types.IdentityType.AGENT_IDENTITY`) 모드로 연동하여 배포하고 서빙하는 환경을 제공합니다.

---

## 🔌 다른 MCP 서버로 확장 및 전환 연동 가이드

Agent Registry에 등록된 다른 MCP 서버로 교체하거나 추가 연동하려면 Agent Registry 에서 MCP 서버 ID 를 확인 후, 다음을 수정 후 Agent Instruction 을 맞게 수정합니다.

`agent.py` 파일의 `mcl_server_name` 변수를 원하는 MCP Server의 ID 정보로 교체합니다.

---

## 🛠️ 핵심 트러블슈팅: AGENT_IDENTITY 교착 상태 해결

### 1. 문제 발생 원인
* 에이전트를 `AGENT_IDENTITY` 방식으로 배포하면, 원격 리소스 ID가 실제로 완전 생성되기 전에는 해당 에이전트 전용 고유 Identity(Federated ID)가 부재하므로 사전에 대상 리소스나 MCP에 대한 IAM 권한을 부여할 수 없습니다.
* 하지만 Vertex AI Reasoning Engine은 배포 프로세스 완료 직전 부트스트랩 단계에서 `agent.py` 코드를 컨테이너에 로드(import)하여 헬스체크를 수행합니다.
* 이때 최상위(global) 스코프에 정의된 `get_mcp_toolset`이 즉시 실행되면서, **아직 권한 바인딩을 받지 못한 상태에서 Agent Registry API를 노크**하게 됩니다. 이로 인해 `403 Permission Denied` 예외가 발생하고 배포 프로세스가 즉시 실패(`failed to start and cannot serve traffic`)하는 닭과 달걀의 교착 상태가 발생합니다.

### 2. 해결 방안 (Guarded MCP Toolset Load)
`agent.py` 최상위 레벨의 `get_mcp_toolset` 획득 호출부를 안정적인 `try-except` 예외 완충 장치로 감쌉니다. 이로써 부트스트랩 시점의 불가피한 인가 거부 예외는 안전하게 경고 로그만 남기고 넘어가며, 배포 완료 후 본격 서빙 요청 시점에 정상적으로 동작할 수 있도록 가드합니다.

```python
# Guard MCP toolset load during remote container bootstrap phase (to avoid chicken-egg IAM Permission Denied loop under AGENT_IDENTITY)
try:
    mcp_toolset = registry.get_mcp_toolset(mcp_server_name=mcl_server_name)
except Exception as e:
    print(f"Warning: Bypassing MCP toolset load error (normal under AGENT_IDENTITY before IAM assignment): {e}")
    mcp_toolset = None
```

---

## 🚀 배포 및 권한 설정 가이드

### 1. Agent Runtime 에 배포

```bash
uv run python agent_runtime.py
```
* 배포가 완료되면 콘솔 창에 **Reasoning Engine Resource Name**과 **Agent Identity** 정보가 출력됩니다.

### 2. Agent Identity에 대한 GCP IAM 권한 할당 (필수)
배포 완료 후, 최종 출력된 에이전트의 고유 Identity가 연동된 서비스(Storage, BigQuery, Vertex AI 등)에 직접 인가될 수 있도록 권한을 할당합니다.

> [!WARNING]
> Agent Identity 바인딩 시에는 `user`나 `serviceAccount` 대신, 반드시 **Workload Identity URI 형식(`principal://`)**을 member 인자로 지정해야 오류가 나지 않습니다.

```bash
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="principal://[EFFECTIVE_IDENTITY_URI]" \
    --role="roles/bigquery.dataViewer"
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="principal://[EFFECTIVE_IDENTITY_URI]" \
    --role="roles/bigquery.jobUser"
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="principal://[EFFECTIVE_IDENTITY_URI]" \
    --role="roles/storage.objectAdmin"
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="principal://[EFFECTIVE_IDENTITY_URI]" \
    --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="principal://[EFFECTIVE_IDENTITY_URI]" \
    --role="roles/roles/mcp.toolUser"
```

---

## 🔍 테스트

API를 직접 호출하기 위한 세션 생성 등의 기본 절차는 최상위 `README.md`의 [공통 API 호출 테스트 가이드](../README.md#🔍-5-공통-api-호출-테스트-가이드)를 참고하세요.

### 테스트 쿼리 예시

세션이 생성된 후, 발급받은 `SESSION_ID`와 `REASONING_ENGINE_ID`를 환경 변수로 등록하고 아래와 같이 질문을 던져볼 수 있습니다.

```bash
export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")

curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  https://us-central1-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}:streamQuery \
  -d '{
    "class_method": "async_stream_query",
    "input": {
      "user_id": "test_user",
      "session_id": "'"${SESSION_ID}"'",
      "message": "현재 빅쿼리의 dataset 리스트 알려줘."
    }
  }'
```
