# Skill Registry 로 부타 Agent Skill 을 조회하여 동작하는 AI Agent

## 🚀 Agent Runtime 배포를 위한 기본 설정

### 1. 환경 변수 설정
배포에 사용할 Google Cloud Project ID, Staging용 Cloud Storage 버킷 URI, 그리고 서비스 계정 이름을 정의합니다.

```bash
cd ~/agent_platform/skill_registry
```

```bash
export PROJECT_ID="YOUR_PROJECT_ID"
export STAGING_BUCKET_URI="gs://YOUR_STAGING_BUCKET_URI"

export SERVICE_ACCOUNT="skill-registry-sa"
```

#### 2. 서비스 계정 생성 및 권한 설정
```bash
# 서비스 계정 이메일 주소 정의 (자동 매칭)
export SA_EMAIL="${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"

# 서비스 계정 생성
gcloud iam service-accounts create ${SERVICE_ACCOUNT} \
    --description="Service account for Agent Registry deployment" \
    --display-name="skill-registry-sa"

# Cloud Trace 권한 부여 for Agent Trace
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/cloudtrace.user"

# Cloud Trace 권한 부여 for Agent Trace
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/cloudtrace.agent"

# Cloud Logging 권한 부여 for Agent Trace
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/logging.viewer"

# Cloud Logging 권한 부여
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/logging.logWriter"

# Vertex AI API 사용 권한 부여
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/serviceusage.serviceUsageConsumer"
```

### 3. `.env` 파일 생성 및 서비스 계정 추가
부모 디렉토리의 환경 변수 템플릿(`.env.template`)을 참조하여 프로젝트 정보를 치환한 로컬 `.env` 파일을 생성하고, 배포에 사용할 서비스 계정 이메일 변수를 안전하게 등록합니다.

```bash
# 1. 환경 변수 템플릿을 치환하여 로컬 .env 생성 (agent_registry 디렉토리 내부에서 실행)
sed -e "s|your-project-id|${PROJECT_ID}|g" \
    -e "s|your-gcs-bucket|${STAGING_BUCKET_URI}|g" \
    ../.env.template > .env

# 2. 서비스 계정 이메일을 배포 환경 변수로 추가 등록
echo "SERVICE_ACCOUNT=${SA_EMAIL}" >> .env

# 3. 설정이 정상적으로 적용되었는지 확인
cat .env
```

---

## 🚀 Agent Runtime 배포

아래의 명령어를 실행하여 에이전트를 Vertex AI Agent Runtime에 성공적으로 배포합니다.
```bash
uv run python agent_runtime.py
```

---


## 🔍 테스트

배포 완료 후 반환받은 `REASONING_ENGINE_ID`를 이용하여 에이전트와 대화를 시작하고 동작을 직접 검증합니다.

### 1. 세션 생성
새로운 세션을 생성하여 대화를 준비합니다.
```bash
export REASONING_ENGINE_ID="[배포 후 발급받은 REASONING_ENGINE_ID]"
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

### 2. 쿼리 실행 (대화 테스트)
세션 생성 성공 시 전달받은 `SESSION_ID`를 등록하여 Skill Registry의 플레이북 지식을 RAG 검색 및 지식 기반 답변으로 유도하는 질문을 에이전트에게 던져봅니다.
```bash
export SESSION_ID="[위 단계에서 발급받은 SESSION_ID]"

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
