# Agent Registry MCP 원격 연동 가이드 (AGENT_IDENTITY)

이 프로젝트는 **GCP Agent Registry**에 등록된 **MCP(Model Context Protocol)** 도구 세트를 원격 **Vertex AI Reasoning Engine**과 고유 아이덴티티(`types.IdentityType.AGENT_IDENTITY`) 모드로 연동하여 배포하고 서빙하는 환경을 제공합니다.

> [!NOTE]
> **실제 연동된 MCP 정보 교정**
> * 현재 `agent.py` 코드에 기본 하드코딩된 `mcl_server_name` 변수 값(`agentregistry-00000000-0000-0000-2039-99a6285dcb61`)은 **BigQuery MCP**가 아닌 **Cloud Storage (GCS) MCP** 서버입니다.
> * 코드 상의 에이전트 정의(`bq_mcp_agent`)와 페르소나 설명은 빅데이터 분석을 유도하고 있으나, 실제 활성화되는 도구셋은 버킷 및 객체 관리용 GCS 툴셋입니다.
> * 다른 GCP MCP 서버(예: 실제 BigQuery MCP)로 전환하여 연동하려면 아래 **[🔌 다른 MCP 서버로 확장 및 전환 연동 가이드]** 항목에 따라 코드를 수정하십시오.

---

## 📂 디렉터리 구조

```
agent_registry_mcp/
├── pyproject.toml          # 패키지 및 의존성 명세 (a2a-sdk, google-adk 등 포함)
├── agent.py                # Agent Registry 기반 MCP 도구 및 에이전트 페르소나 정의
└── agent_runtime.py        # Vertex AI Agent Runtime 원격 배포 스크립트
```

---

## 🔌 다른 MCP 서버로 확장 및 전환 연동 가이드

Agent Registry에 등록된 다른 MCP 서버로 교체하거나 추가 연동하려면 **MCP 서버 탐색 -> ID 교체 -> 에이전트 성격 수정**의 3단계를 거칩니다.

### 1단계: Agent Registry에 등록된 MCP 서버 ID 탐색
프로젝트 환경의 가상환경 내에서 아래 Python 스크립트를 작성하여 기동하면, 현재 사용 가능한 모든 MCP 서버의 고유 ID 리스트와 제공 도구 목록을 조회할 수 있습니다.

```python
import os
from google.adk.integrations.agent_registry import AgentRegistry

# Registry 클라이언트 초기화
registry = AgentRegistry(
    project_id=os.environ.get("GOOGLE_CLOUD_PROJECT", "gcp-sandbox-kwlee"),
    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
)

# 등록된 모든 MCP 서버 목록 출력
servers = registry.list_mcp_servers()
for s in servers.get('mcpServers', []):
    short_id = s.get('name').split('/')[-1]
    print(f"[{s.get('displayName')}] ID: {short_id} - {s.get('description')}")
```

#### 💡 Agent Registry 주요 내장 MCP 서버 ID 리스트
자주 사용하는 핵심 MCP 서비스 ID들을 미리 제공합니다. 원하는 도구셋에 맞는 ID를 선택하십시오.

| 대상 GCP 서비스 | Display Name | MCP Server ID (Short ID) | 제공되는 주요 도구 |
| :--- | :--- | :--- | :--- |
| **Cloud Storage (GCS)** | `storage.googleapis.com` | `agentregistry-00000000-0000-0000-2039-99a6285dcb61` | `list_buckets`, `list_objects`, `read_text`, `write_text` 등 |
| **BigQuery (BQ)** | `bigquery.googleapis.com` | `agentregistry-00000000-0000-0000-3781-81d342859334` | `list_datasets`, `list_tables`, `query`, `get_table_schema` 등 |
| **Cloud SQL** | `cloud-sql` | `agentregistry-00000000-0000-0000-2c61-77e00c7e4574` | 데이터베이스 관리, 인스턴스 조회 및 관리 도구 |
| **Vertex AI** | `aiplatform.googleapis.com` | `agentregistry-00000000-0000-0000-5df7-d125061c8dc3` | 모델 튜닝, 평가, 배포 엔드포인트 관리 도구 |
| **Cloud Logging** | `logging.googleapis.com` | `agentregistry-00000000-0000-0000-33ac-b82d3e783371` | 로그 엔트리 조회 및 분석 도구 |
| **Cloud Run** | `run.googleapis.com` | `agentregistry-00000000-0000-0000-0c34-a2d85a151b0f` | Cloud Run 서비스 및 작업 상태 관리 도구 |
| **Google Kubernetes Engine** | `container.googleapis.com` | `agentregistry-00000000-0000-0000-861b-11c2ceb07996` | GKE 클러스터 정보 및 워크로드 관리 도구 |

### 2단계: `agent.py` 코드 내 서버 ID 수정
`agent.py` 파일의 상단부에 정의된 `mcl_server_name` 변수를 원하는 MCP Server의 ID 정보로 교체합니다.

> [!IMPORTANT]
> **수정 지점 (`agent.py` L39 부근):**
> ```python
> # [수정 전: Storage MCP 서버]
> # mcl_server_name = "mcpServers/agentregistry-00000000-0000-0000-2039-99a6285dcb61"
> 
> # [수정 후: BigQuery MCP 서버로 변경할 경우]
> mcl_server_name = "mcpServers/agentregistry-00000000-0000-0000-3781-81d342859334"
> ```

### 3단계: 에이전트 이름 및 페르소나 동기화
선택한 MCP 도구셋에 걸맞은 성격과 기능을 갖추도록 에이전트 정의부(`root_agent`)의 `name`과 `instruction` 가이드를 알맞게 보정합니다.

```python
root_agent = Agent(
    name="bq_mcp_agent",  # 역할에 알맞은 에이전트 명 지정
    model="gemini-3.5-flash",
    instruction=(
        "You are an expert Data Science Agent. "
        "Your goal is to query enterprise BigQuery datasets, analyze the data... "
        # 연동한 MCP 도구 활용 방식을 명시하는 System Instruction 구성
    ),
    tools=[t for t in [mcp_toolset, PreloadMemoryTool()] if t is not None],
    after_agent_callback=generate_memories_callback,
)
```

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

## 🚀 원격 배포 및 권한 설정 가이드

### 1. 원격 Reasoning Engine 배포
의존성 주입이 완료된 Vertex AI 원격 환경으로 에이전트 소스를 배포합니다:

```bash
uv run python agent_runtime.py
```
* 배포가 완료되면 콘솔 창에 **Reasoning Engine Resource Name**과 **Effective Identity (Federated ID URI)** 주소가 최종 발급되어 출력됩니다.

### 2. 고유 Identity에 대한 GCP IAM 권한 할당 (필수)
배포 완료 후, 최종 출력된 에이전트의 고유 Identity가 연동된 서비스(Storage, BigQuery, Vertex AI 등)에 직접 인가될 수 있도록 권한을 할당합니다.

> [!WARNING]
> Federated Identity 바인딩 시에는 `user`나 `serviceAccount` 대신, 반드시 **Workload Identity URI 형식(`principal://`)**을 member 인자로 지정해야 오류가 나지 않습니다.

```bash
# 1. Cloud Storage 버킷 및 객체 관리 권한 부여 (현재 사용 중인 Storage MCP용)
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="principal://[EFFECTIVE_IDENTITY_URI]" \
    --role="roles/storage.objectAdmin"

# 2. BigQuery 데이터 조회 및 쿼리 실행 권한 부여 (BigQuery MCP로 전환할 경우)
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="principal://[EFFECTIVE_IDENTITY_URI]" \
    --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="principal://[EFFECTIVE_IDENTITY_URI]" \
    --role="roles/bigquery.jobUser"

# 3. Vertex AI API 호출 권한 부여 (공통)
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="principal://[EFFECTIVE_IDENTITY_URI]" \
    --role="roles/aiplatform.user"
```

---

## 🔍 라이브 서빙 검증

원격 배포와 IAM 권한 바인딩이 성료되면 원격 컨테이너 내부의 에이전트는 기동 시점에 MCP 도구셋을 정상 조작할 수 있는 권한을 얻습니다. 아래와 같이 `vertexai` v1beta1 API의 `stream_query` 규격을 이용하여 즉시 서빙 동작을 검증할 수 있습니다:

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
    # 현재 설정(Storage MCP)에 특화된 동작 확인
    message="내 버킷의 오브젝트 목록을 조회해 줄 수 있어?" 
)

for chunk in response_stream:
    print(chunk, end="", flush=True)
```
