# Vertex AI Agent Platform - Agent Identity

이 프로젝트는 **Vertex AI Agent Platform(Agent Engines)** 에 `google-adk` 기반 에이전트를 배포할 때, 에이전트 고유의 독립적인 서비스 ID인 **Agent Identity**를 설정하여 배포하는 방법을 안내합니다.

일반적으로 에이전트가 외부 서비스나 GCP 리소스를 호출할 때 호출자의 권한을 위임받는 대신, 에이전트 자체에 부여된 독립적인 서비스 ID(**Agent-own Identity**)를 사용하여 안전하고 세밀하게 IAM 권한을 제어할 수 있습니다.

---

## 1. 프로젝트 구조 및 요구 사항

- **[run_agent.py](file:///usr/local/google/home/kiwonlee/workspace/agents/agent_platform/agent_identity/run_agent.py)**: 원격 Vertex AI Agent Platform에 에이전트를 배포하고 `AGENT_IDENTITY`를 설정하는 실행 스크립트
- **[agent.py](file:///usr/local/google/home/kiwonlee/workspace/agents/agent_platform/agent_identity/agent.py)**: `google.adk.agents.llm_agent.Agent` 기반으로 작성된 샘플 에이전트
- **[pyproject.toml](file:///usr/local/google/home/kiwonlee/workspace/agents/agent_platform/agent_identity/pyproject.toml)**: 패키지 의존성 및 Python 버전 설정 (`>=3.13`)

### 환경 변수 설정 (`.env`)
상위 디렉토리 또는 프로젝트 내 `.env` 파일에 GCP 프로젝트 ID를 설정해야 합니다.
```env
GOOGLE_CLOUD_PROJECT="your-google-cloud-project-id"
```

---

## 2. 주요 개념 및 설정: Agent Identity

[run_agent.py](file:///usr/local/google/home/kiwonlee/workspace/agents/agent_platform/agent_identity/run_agent.py) 스크립트에서는 다음과 같은 핵심 설정을 통해 에이전트 자체 ID를 부여합니다.

### ① `v1beta1` API 버전 사용
Agent Identity 스펙을 정상적으로 지원하기 위해 `vertexai.Client` 초기화 시 `v1beta1` API 버전을 명시적으로 지정합니다.
```python
client = vertexai.Client(
    project=PROJECT_ID,
    location=LOCATION,
    http_options=dict(api_version="v1beta1")
)
```

### ② `IdentityType.AGENT_IDENTITY` 지정
`client.agent_engines.create()` 호출 시 `config`의 `identity_type`을 `AGENT_IDENTITY`로 설정합니다.
```python
remote_app = client.agent_engines.create(
    agent=app,
    config={
        "display_name": "Agent Identity",
        "identity_type": types.IdentityType.AGENT_IDENTITY,
        # ...
    }
)
```

### ③ 토큰 공유 방지(Prevent Agent Token Sharing) 정책 예외 설정
에이전트가 자체 ID를 사용하여 GCP 서비스 등을 인증할 때, 토큰 공유 방지 정책으로 인한 `401 Unauthorized` 에러를 방지하기 위해 환경 변수로 해당 정책을 비활성화(`False`)합니다.
```python
"env_vars": {
    "GOOGLE_API_PREVENT_AGENT_TOKEN_SHARING_FOR_GCP_SERVICES": "False",
}
```

> **관련 공식 문서**:
> - [에이전트 자체 ID (Agent-own identity) 사용 안내](https://docs.cloud.google.com/iam/docs/auth-agent-own-identity?hl=ko#opt-out-caa)
> - [인증 관리자 401 오류 문제 해결](https://docs.cloud.google.com/iam/docs/troubleshoot-auth-manager?hl=ko#401-error)

---

## 3. 실행 방법 및 결과 확인

### 배포 실행
```bash
uv run run_agent.py
```

### 출력 예시
배포가 성공적으로 완료되면, 배포된 원격 에이전트의 리소스 이름과 함께 할당된 **유효 ID(`effective_identity`)**를 확인할 수 있습니다.

```text
Initializing Vertex AI Client (Project: my-gcp-project, Location: us-central1)...
Wrapping agent in AdkApp...

✅ Deployment successful!
Remote Agent Name: projects/123456789/locations/us-central1/agents/agent-xxxx
Effective Identity: serviceAccount:agent-xxxx@my-gcp-project.iam.gserviceaccount.com
```

- **`Effective Identity`**: 배포된 에이전트가 향후 BigQuery, Cloud Storage 등 다른 GCP 리소스나 외부 API에 접근할 때 사용하는 서비스 계정(Service Account)입니다.
- 이 서비스 계정에 필요한 최소 IAM 역할을 부여함으로써 **최소 권한 원칙(Least Privilege)** 을 유지할 수 있습니다.
