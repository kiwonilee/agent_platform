# Agent Registry & BigQuery MCP 에이전트

이 프로젝트는 **GCP Agent Registry**와 **MCP(Model Context Protocol)** 도구 세트를 활용하여 엔터프라이즈 데이터셋을 조회하고 SQL 분석 및 요약 리포트를 생성하는 고성능 단일 에이전트 아키텍처를 안내합니다.

Google **ADK (Agent Development Kit)** 프레임워크를 기반으로 구축되었으며, 외부 설정 파일(`.env`) 없이 Python 코드 내에서 직접 설정을 관리하는 간결하고 강력한 구조를 채택했습니다.

---

## 🚀 주요 기능

* **관리형 MCP 통합**: GCP Agent Registry를 네이티브하게 호출하여 원격 BigQuery MCP 도구 세트를 단일 흐름으로 안전하게 장착합니다.
* **메모리 뱅크 연동**: 프로덕션 Agent Engine 환경에서 크로스 세션(Cross-session) 대화 상태를 연속 유지하기 위한 세션/메모리 서비스 연결을 지원합니다.
* **통합 패키지 관리**: `uv`를 통해 빠르고 견고하게 가상 환경 및 패키지 의존성을 격리·관리합니다.
* **원클릭 프로덕션 배포**: [agent_runtime.py](file:///usr/local/google/home/kiwonlee/workspace/agents/agent_platform/agent_registry_mcp/agent_runtime.py) 스크립트를 통해 Vertex AI Agent Engine에 단 한 번의 실행으로 즉시 배포됩니다.

---

## 📁 디렉터리 구조

```
agent_registry_mcp/
├── README.md               # 개발자 안내 및 명령어 가이드
├── pyproject.toml          # 패키지 및 의존성 명세
├── uv.lock                 # 잠금 처리된 패키지 버전
├── agent.py                # 단일 에이전트 및 MCP 도구 정의
└── agent_runtime.py        # Vertex AI Agent Runtime 원클릭 프로덕션 배포 스크립트
```

---

## ⚙️ 설정 및 인증

### 1. 인증 스코프 (필수)
에이전트가 GCP Agent Registry를 호출하여 MCP 도구를 가져오려면 로컬 환경 인증 시 반드시 `cloud-platform` 스코프를 포함해야 `403 Forbidden` 에러를 방지할 수 있습니다.

```bash
gcloud auth application-default login --scopes=https://www.googleapis.com/auth/cloud-platform
```

### 2. 패키지 의존성 동기화
`uv`를 사용하여 모든 ADK 및 MCP 관련 의존성을 동기화하고 활성화합니다:

```bash
uv sync
source .venv/bin/activate
```

---

## 💻 로컬 실행 명령어

`agent_registry_mcp/` 폴더 내에서 아래 명령어들을 실행하여 로컬 대화형 세션을 시작할 수 있습니다:

### A. 대화형 CLI 모드 실행
터미널 창에서 실시간으로 대화하며 BigQuery 조회 및 분석을 수행합니다:
```bash
uv run adk run .
```

### B. 개발자 웹 UI 실행
백그라운드에 FastAPI 서버를 띄우고 직관적인 웹 채팅 인터페이스를 엽니다:
```bash
uv run adk web .
```
실행 후 터미널에 출력된 URL(기본값 `http://127.0.0.1:8086/dev-ui/`)로 접속합니다.

---

## 🚀 Vertex AI Agent Runtime 프로덕션 배포

### 1. 배포 스크립트 실행
[agent_runtime.py](file:///usr/local/google/home/kiwonlee/workspace/agents/agent_platform/agent_registry_mcp/agent_runtime.py) 스크립트를 실행하여 관리형 서버리스 환경인 Vertex AI Agent Engine에 배포합니다:

```bash
uv run python agent_runtime.py
```

배포가 성공적으로 완료되면 콘솔에 원격 에이전트의 리소스 URI와 할당된 **Effective Identity(유효 ID)** 가 출력됩니다.
출력된 리소스 URI를 통해 언제든 원격 데이터 분석 세션을 호출할 수 있습니다.
