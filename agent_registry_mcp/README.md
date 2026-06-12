# Agent Registry & BigQuery MCP 에이전트 (AGENT_IDENTITY)

이 프로젝트는 **GCP Agent Registry**와 **MCP(Model Context Protocol)** 도구 세트를 사용하여 엔터프라이즈 BigQuery 데이터셋을 분석하는 에이전트를 **Vertex AI Reasoning Engine**에 고유 아이덴티티(`types.IdentityType.AGENT_IDENTITY`) 모드로 안전하게 배포하고 서빙하는 설정을 다룹니다.

---

## 📂 디렉터리 구조

```
agent_registry_mcp/
├── pyproject.toml          # 패키지 및 의존성 명세 (a2a-sdk, google-adk 등 포함)
├── agent.py                # MCP 도구 및 데이터 분석 에이전트 정의
└── agent_runtime.py        # Vertex AI Agent Runtime 원격 배포 스크립트
```

---

## 🛠️ 핵심 트러블슈팅: AGENT_IDENTITY 교착 상태 해결

### 1. 문제 발생 원인
* 에이전트를 `AGENT_IDENTITY` 방식으로 배포하면, 최종 리소스 ID가 생성되기 전까지는 해당 에이전트의 고유 Identity String이 미정이므로 사전에 IAM 권한을 부여할 수 없습니다.
* 하지만 Vertex AI Reasoning Engine은 배포 완료 직전 검증 단계에서 `agent.py` 코드를 메모리에 로드(import)하여 기동성 테스트를 진행합니다.
* 이때 최상위(global) 레벨에 정의된 `get_mcp_toolset`이 정적으로 즉시 호출되면서 **아무런 IAM 권한이 없는 상태에서 GCP API를 호출**하게 되며, 결과적으로 `403 Permission Denied` 예외를 발생시키고 배포 자체가 영구 실패(`failed to start and cannot serve traffic`)하는 닭과 달걀의 교착 상태가 발생합니다.

### 2. 해결 방안 (Guarded MCP Toolset Load)
`agent.py` 최상위의 `get_mcp_toolset` 호출을 가벼운 `try-except` 구조로 감싸, 부트스트랩 검증 시의 불가피한 예외를 안정적으로 무시하여 배포를 완수할 수 있게 가드합니다:

```python
# Guard MCP toolset load during remote container bootstrap phase (to avoid chicken-egg IAM Permission Denied loop under AGENT_IDENTITY)
try:
    mcp_toolset = registry.get_mcp_toolset(mcp_server_name=mcl_server_name)
except Exception as e:
    print(f"Warning: Bypassing MCP toolset load error (normal under AGENT_IDENTITY before IAM assignment): {e}")
    mcp_toolset = None
```

---

## 🚀 원격 배포 및 권한 설정 가이드

### 1. 원격 Reasoning Engine 배포
아래 명령어를 통해 가상환경 의존성을 주입하여 원격 Vertex AI Agent Runtime에 무사히 배포를 보냅니다:

```bash
uv run python agent_runtime.py
```
* 성공적으로 완료되면 콘솔에 생성된 **Reasoning Engine Resource Name**과 **Effective Identity(Federated ID)** 주소가 출력됩니다.

### 2. 고유 Identity에 대한 GCP IAM 권한 할당 (필수)
배포가 끝난 뒤, 발급된 고유 Identity가 실제로 BigQuery 및 AI Platform에 접근할 수 있도록 권한을 바인딩합니다. 
Federated Identity에 권한을 할당할 때는 일반 `user`나 `serviceAccount` 접두사 대신, 아래와 같이 **정확한 Workload Identity 형식(`principal://`)**을 사용해야 타입 에러를 방지할 수 있습니다.

```bash
# 1. BigQuery 데이터 조회 권한 부여
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="principal://[EFFECTIVE_IDENTITY_URI]" \
    --role="roles/bigquery.dataViewer"

# 2. BigQuery 쿼리 실행(Job) 권한 부여
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="principal://[EFFECTIVE_IDENTITY_URI]" \
    --role="roles/bigquery.jobUser"

# 3. Vertex AI API 호출 권한 부여
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="principal://[EFFECTIVE_IDENTITY_URI]" \
    --role="roles/aiplatform.user"

# 4. Storage 버킷 객체 관리 권한 부여
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="principal://[EFFECTIVE_IDENTITY_URI]" \
    --role="roles/storage.objectAdmin"
```

---

## 🔍 라이브 서빙 검증

IAM 권한 부여가 정상적으로 마무리되면, 원격 에이전트는 무사히 기동되어 MCP 툴셋 조회를 완료하고 활성화됩니다. `vertexai` 클라이언트를 초기화하여 `stream_query` API 규격으로 에이전트 연동 상태를 즉시 점검할 수 있습니다:

```python
import vertexai

client = vertexai.Client(
    project="[PROJECT_ID]",
    location="us-central1",
    http_options=dict(api_version="v1beta1")
)

remote_agent = client.agent_engines.get(name="[REASONING_ENGINE_RESOURCE_NAME]")
response_stream = remote_agent.stream_query(
    user_id="verifier",
    session_id="sess_verify",
    message="Enterprise BigQuery 데이터셋 분석 준비가 완료되었습니까?"
)

for chunk in response_stream:
    print(chunk, end="", flush=True)
```
