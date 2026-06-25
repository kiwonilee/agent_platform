# Skill Registry 연동 (#Agent Identity, #Skill Registry, #Agent Runtime)

이 프로젝트는 **Gemini Enterprise Agent Platform Skill Registry**에 등록된 플레이북 스킬들을 원격 **Agent Runtime**과 Agent Identity (`types.IdentityType.AGENT_IDENTITY`) 모드로 연동하여 배포하고 서빙하는 환경을 제공합니다.

---

## 🚀 배포 및 권한 설정 가이드

### 1. Agent Runtime에 배포
`agent_platform/skill_registry/` 디렉터리 내에서 아래 배포 명령을 실행합니다:

```bash
uv run agent_runtime.py
```
* 배포가 성공하면 콘솔 창에 **Reasoning Engine Resource Name (Remote Agent Name)**과 **Agent Identity (Federated ID)** 정보가 출력됩니다.

### 2. Agent Identity에 대한 GCP IAM 권한 할당 (필수)
배포 완료 후, 최종 출력된 에이전트의 고유 Identity가 Skill Registry 데이터베이스에 직접 접근하고 쿼리를 수행할 수 있도록 필요한 권한을 할당합니다.

> [!WARNING]
> Agent Identity 바인딩 시에는 `user`나 `serviceAccount` 대신, 반드시 **Workload Identity URI 형식(`principal://`)**을 member 인자로 지정해야 오류가 나지 않습니다.

```bash
export PROJECT_ID="[GCP 프로젝트 ID]"
export EFFECTIVE_IDENTITY="[출력된 Agent Identity 값 (e.g. projects/...)]"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="principal://${EFFECTIVE_IDENTITY}" \
    --role="roles/aiplatform.viewer"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="principal://${EFFECTIVE_IDENTITY}" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="principal://${EFFECTIVE_IDENTITY}" \
    --role="roles/serviceusage.serviceUsageConsumer"
```

---

## 🔍 테스트

API를 직접 호출하기 위한 세션 생성 등의 기본 절차는 최상위 `README.md`의 [공통 API 호출 테스트 가이드](../README.md#🔍-5-공통-api-호출-테스트-가이드)를 참고하세요.

### 테스트 쿼리 예시 (스킬 기반 처리 테스트)

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
      "message": "GKE 의 Cluster Upgrade 에 대한 Best Practice 에 대해서 알려줘"
    }
  }'
```

---

## 🛠️ Gemini Enterprise Skill Registry 관리 CLI 도구

SRE 관리자가 원격 스킬 레지스트리(Playbook Database) 내의 지식을 등록, 조회, 삭제 및 RAG 검색 테스트를 수행할 때 사용하는 CLI 툴 가이드입니다.

### A. 등록된 전체 플레이북 스킬 리스트 조회
```bash
uv run skill_registry.py list
```

### B. 신규 플레이북 스킬 생성 및 등록
```bash
uv run skill_registry.py create \
    --display-name "GKE Node Upgrade Playbook" \
    --description "Step-by-step handbook to perform safe GKE node upgrades" \
    --local-path "path/to/playbooks/gke_upgrade"
```

### C. 특정 플레이북 스킬 세부 명세 조회
```bash
uv run skill_registry.py get --skill-name "[스킬ID 또는 리소스 고유URI]"
```

### D. 등록된 스킬 삭제
```bash
uv run skill_registry.py delete --skill-name "[스킬ID 또는 리소스 고유URI]"
```

### E. 플레이북 지식 검색 테스트 (RAG Search)
```bash
uv run skill_registry.py retrieve --query "GKE node upgrade" --top-k 2
```

### F. GitHub 리포지토리로부터 플레이북 스킬 벌크 임포트
```bash
uv run skill_registry.py import --github-url "https://github.com/google/skills"
```
