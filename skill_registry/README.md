# Google Cloud AI Ops Orchestrator

구글 **ADK (Agent Development Kit)** 프레임워크를 기반으로 설계된 엔터프라이즈급 초고속 **단일 에이전트 AI Ops 아키텍트**입니다. 본 에이전트는 **GCP MCP (Model Context Protocol)** 도구 세트와 **Gemini 엔터프라이즈 에이전트 플랫폼 스킬 레지스트리**를 직접 제어하여 구글 클라우드 리소스를 실시간으로 모니터링, 분석 및 분석 트러블슈팅합니다.

---

## 🚀 핵심 기능

*   **다이렉트 도구 호출 구조**: 다중 에이전트 간의 불필요한 라우팅을 단일 초고속 오케스트레이터 에이전트로 통합하여 실제 GCP 명령어들을 즉각 실행하므로 속도가 3배 이상 빠르고 비용 효율적입니다.
*   **7대 active GCP SRE 서비스**: GKE, Cloud Run, Logging, Monitoring, Network Management, Gemini Cloud Assist, Error Reporting 등 총 53개 이상의 SRE 인프라 제어 도구를 완벽 지원합니다.
*   **스킬 자동 디스커버리**: 원격 스킬 레지스트리 데이터베이스에 저장된 특화 SRE 플레이북(Handbooks)을 의미론적으로 검색하여 동적으로 실시간 호출하는 도구를 탑재하고 있습니다.
*   **통합 실행 로깅**: 강력하고 안전한 콜백 함수를 내장하여 터미널 환경에서 에이전트가 도구 및 스킬을 실행할 때마다 정확한 파라미터 정보와 결과를 실시간 터미널 로그로 완벽히 출력합니다.
*   **깔끔한 패키지 격리**: 패키지 네임스페이스 바인딩 기법을 활용해 번잡한 기동 전용 스크립트들을 `agent_platform/` 하위 디렉터리로 완전히 격리하여 메인 루트 경로를 극도로 깔끔하게 유지합니다.

---

## 📁 리포지토리 디렉터리 구조

```
google_cloud_ops_agent/
├── README.md               # 개발 설명서 및 명령어 기술 문서
├── pyproject.toml          # 파이썬 패키지 의존성 정의 토글 파일
├── uv.lock                 # 잠금 처리된 의존성 파일
├── __init__.py             # 에이전트 패키지 진입 파일
├── agent.py                # 메인 에이전트 정의 및 모니터링 콜백 (패키지 바인딩)
├── tools.py                # 절차적 GCP MCP 도구 세트 로더 (자기 완결형 구조)
├── skills.py               # RAG 플레이북 스킬 실시간 탐색 도구 (패키지 바인딩)
└── agent_platform/         # AgentPlatform SRE 행정 및 배포 관리 패키지
    ├── runtime.py          # 프로덕션 원스톱 원클릭 배포 스크립트
    └── skill_registry.py   # RAG 스킬 플레이북 등록/삭제 관리 CLI 툴
```

---

## ⚙️ 초기 설치 및 환경 설정

### 1. 환경 설정 파일 생성 (`.env`)
`google_cloud_ops_agent/` 폴더 루트에 제공된 `.env.template` 파일을 복사하여 `.env` 파일을 생성하고 필요한 환경 변수 값을 설정합니다.
또는 아래 예시와 같이 변수들을 직접 입력할 수 있습니다:

```ini
# 구글 클라우드 프로젝트 환경 설정
GOOGLE_CLOUD_PROJECT="your-googlecloud-project"
GOOGLE_CLOUD_LOCATION="global"
GOOGLE_GENAI_USE_VERTEXAI=TRUE

# SRE 리소스 및 스킬 레지스트리 리전 설정
GCP_RESOURCES_LOCATION="us-central1"

# Telemetry for ADK
GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true
OTEL_SEMCONV_STABILITY_OPT_IN="gen_ai_latest_experimental"
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=EVENT_ONLY
```

### 2. 가상환경 구동 및 의존성 검증
가상환경이 켜져 있고 ADK의 핵심 라이브러리들이 정상 셋업되었는지 확인합니다:

```bash
# 가상 환경 구동
uv sync
source .venv/bin/activate
```


<br/>

---
---

<br/>

## 💻 로컬 실행

대화형 AI Ops 에이전트를 기동하고 상호작용하려면 `google_cloud_ops_agent/` 디렉터리 내부에서 아래 명령어를 직접 날려 가동합니다.


## ⚙️ 핵심 피처 플래그(Feature Flags) 동작 원리 기술 설명

*   **`--disable_features=JSON_SCHEMA_FOR_FUNC_DECL`** *(치명적인 컨텍스트 폭발 우회 플래그)*:
    *   **도입 이유**: ADK의 실험용 기능인 JSON 스키마 자동 파서 모듈은 GKE나 Kubernetes API처럼 무한 루프성 Pydantic 계층 구조를 지닌 리소스 명세를 만날 경우, 이를 해석하기 위해 스키마를 무한대로 복제/전개하는 치명적인 버그가 있습니다.
    *   **효과**: 이 옵션을 반드시 기입해 꺼주면 에이전트가 표준 평탄형(Flat) 스키마 선언 구조로 안정적으로 동작하여, 기존의 프롬프트 토큰 누수량(**약 130만 토큰**)을 미세한 깃털 등급 수준(**약 1만 토큰**)으로 극적으로 다이어트시켜 에러 없는 엄청난 초고속 응답 속도를 보장합니다.
*   **`--enable_features=SKILL_TOOLSET`** *(스킬 탐색기)*:
    *   **도입 이유**: 엔터프라이즈 스킬 셋 가동용 모듈을 활성화합니다.
    *   **효과**: 오케스트레이터 에이전트에게 스킬 디스커버리 도구들을 온전히 쥐여주어, 대화 중 원격에 등록된 플레이북(Playbook) 지식을 스스로 검색해서 동적으로 장착하여 가동할 수 있는 자율 행동권이 확보됩니다.

### A. 터미널 대화형 CLI 모드 진입
터미널창에서 실시간 채팅 형태로 에이전트에게 리소스 모니터링 및 조회를 실행하게 하려면:
```bash
adk run --disable_features=JSON_SCHEMA_FOR_FUNC_DECL --enable_features=SKILL_TOOLSET .
```

### B. 대화형 웹 UI 실행
배포용 FastAPI 서버를 백그라운드에 띄우고, 아름다운 웹 채팅 패널 창을 오픈하려면:
```bash
adk web --disable_features=JSON_SCHEMA_FOR_FUNC_DECL --enable_features=SKILL_TOOLSET .
```
서버 부트스트랩이 완료되면 터미널에 출력된 웹 브라우저 주소(기본값 `http://127.0.0.1:8086/dev-ui/`)로 접속합니다.


<br/>

---
---

<br/>

## 🚀 AgentPlatform 배포

서버리스 프로덕션 환경에 에이전트를 상시 구동형 서비스로 안착시키기 위해 구글 **에이전트 플랫폼(Agent Platform - Reasoning Engine)** 서버 인프라에 원클릭 업로드 배포합니다.

### 1. 전용 보안 서비스 계정(SA) 개설 및 IAM 권한 영구 위임
배포용 커스텀 서비스 계정을 생성하고, 에이전트 컨테이너가 내부에서 리소스를 안전하게 조회하고 오픈텔레메트리 성능 로깅을 수행할 수 있도록 권한을 단번에 부여합니다:

```bash
export PROJECT_ID="gcp-sandbox-kwlee"
export SA_EMAIL="google-cloud-ops-agent-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# 1. 서비스 계정 생성
gcloud iam service-accounts create google-cloud-ops-agent-sa \
    --description="Managed Service Account for AI Ops Orchestrator Agent" \
    --display-name="Google Cloud Ops Agent SA"

# 2. 7대 GCP 서비스 조회 권한 부여
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SA_EMAIL}" --role="roles/container.viewer"
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SA_EMAIL}" --role="roles/run.viewer"
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SA_EMAIL}" --role="roles/logging.viewer"
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SA_EMAIL}" --role="roles/monitoring.viewer"
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SA_EMAIL}" --role="roles/aiplatform.user"

# 3. 에이전트의 성능/인프라 OpenTelemetry 모니터링 로그 쓰기 권한 (403 에러 완벽 방지!)
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SA_EMAIL}" --role="roles/logging.logWriter"

# 4. 로컬 아티팩트 임시 보관용 GCS 버킷 읽기/쓰기 권한
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SA_EMAIL}" --role="roles/storage.objectAdmin"
```

### 2. 배포 스크립트 원클릭 실행
`.env` 설정이 완비된 상태에서 전용 통합 배포 자동화 파일인 `agent_platform/runtime.py`를 원클릭 구동합니다:

```bash
uv run agent_platform/runtime.py
```
  
배포가 성공하면 콘솔에 고유 원격 리소스 URI 주소가 출력됩니다: `projects/{project_number}/locations/us-central1/reasoningEngines/{engine_id}`

<br/>

---
---

<br/>

## 🛠️ Gemini Enterprise Skill Registy 관리 도구

> [!NOTE]
> 본 도구는 **AgentPlatform 배포(`runtime.py`) 파이프라인과는 완전히 독립적으로 동작하는 별개의 관리용 CLI 도구**입니다. SRE 관리자가 원격 스킬 레지스트리(Playbook Database) 내의 지식을 상시 등록, 조회, 삭제 및 RAG 검색 테스트를 수행할 때 사용합니다.

SRE 관리자를 위하여, 의미론적으로 탐색하여 동적으로 꺼내 쓸 수 있는 SRE 플레이북 지식 데이터베이스를 제어하는 전용 CLI 도구 `agent_platform/skill_registry.py`를 제공합니다.

`google_cloud_ops_agent/` 디렉터리 내에서 `uv run`을 사용하여 모든 행정 커맨드를 즉시 가동할 수 있습니다:

### A. 등록된 전체 플레이북 스킬 리스트 조회
현재 클라우드 프로젝트의 타깃 리전에 등재되어 동작 중인 모든 플레이북 지식의 목록을 확인합니다:
```bash
uv run agent_platform/skill_registry.py list
```

### B. 신규 플레이북 스킬 생성 및 등록
로컬 경로에 `SKILL.md` 매뉴얼 문서가 작성되어 있는 전용 폴더를 지정해 레지스트리에 새로운 스킬로 밀어 넣습니다:
```bash
uv run agent_platform/skill_registry.py create \
    --display-name "GKE Node Upgrade Playbook" \
    --description "Step-by-step handbook to perform safe GKE node upgrades" \
    --local-path "path/to/playbooks/gke_upgrade"
```

### C. 특정 플레이북 스킬 세부 명세 조회
스킬 데이터베이스를 조회하여 스킬의 구체적인 작동 지침과 메타데이터 사양을 상세히 열람합니다:
```bash
uv run agent_platform/skill_registry.py get --skill-name "[스킬ID 또는 리소스 고유URI]"
```

### D. 등록된 스킬 삭제
더 이상 필요 없거나 수명이 다한 구식 가이드 스킬을 레지스트리 데이터베이스에서 영구 격리 삭제합니다:
```bash
uv run agent_platform/skill_registry.py delete --skill-name "[스킬ID 또는 리소스 고유URI]"
```

### E. 플레이북 지식 검색 테스트 (RAG Search)
등록해 둔 플레이북에 대해 의미론적 질문을 던져 정보가 원하는 가중치대로 정확하게 인출(Retrieval)되는지 시뮬레이션 테스트합니다:
```bash
uv run agent_platform/skill_registry.py retrieve --query "GKE node upgrade" --top-k 2
```

### F. GitHub 리포지토리로부터 플레이북 스킬 벌크 임포트 (Bulk Import)
`SKILL.md` 매뉴얼이 포함된 퍼블릭 GitHub 저장소의 SRE 플레이북 세트를 단 한 번에 자동으로 내려받아, 메타데이터를 자동 파싱하여 레지스트리에 통째로 등록합니다:
```bash
uv run agent_platform/skill_registry.py import --github-url "https://github.com/google/skills"
```

---


---

## 🧹 대화 세션 히스토리 초기화 (개발 디버깅용)

로컬에서 지속적인 빠른 테스트를 거치다가 대화 히스토리 캐시 데이터가 너무 많아져 완전히 리셋하고 깨끗한 첫 턴 상태로 돌리고 싶다면:
```bash
# google_cloud_ops_agent 폴더 내부에서 실행
rm -rf .adk/
```
