# Agent Runtime with MemroyBank

## 🚀 Agent Runtime 배포를 위한 기본 설정

### 1. 환경 변수 및 관련 API 활성화
배포에 사용할 Google Cloud Project ID를 설정하고 필수 API들을 활성화한 후, 배포 관련 환경 변수를 정의합니다.

```bash
cd ~/agent_platform/agent_runtime
```

```bash
gcloud services enable \
    aiplatform.googleapis.com \
    agentregistry.googleapis.com \
    logging.googleapis.com \
    cloudtrace.googleapis.com \
    storage.googleapis.com \
    iam.googleapis.com
```

```bash
export PROJECT_ID="YOUR_PROJECT_ID"
export STAGING_BUCKET_URI="gs://adk-${PROJECT_ID}"
```

### 2. Cloud Storage 버킷 생성
배포 산출물을 저장할 Google Cloud Storage 버킷을 생성합니다. (이미 사용 중인 버킷이 있다면 이 단계는 건너뛰셔도 됩니다.)

```bash
gcloud storage buckets create ${STAGING_BUCKET_URI} --location=us-central1
```

#### 3. `.env` 파일 생성
부모 디렉토리의 환경 변수 템플릿(`.env.template`)을 참조하여 프로젝트 정보를 치환한 로컬 `.env` 파일을 생성합니다.

```bash
# 1. 환경 변수 템플릿을 치환하여 로컬 .env 생성 (agent_runtime 디렉토리 내부에서 실행)
sed -e "s|your-project-id|${PROJECT_ID}|g" \
    -e "s|your-gcs-bucket|${STAGING_BUCKET_URI}|g" \
    ../.env.template > .env

# 2. 설정이 정상적으로 적용되었는지 확인
cat .env
```

---

## 🚀 Agent Runtime 배포

아래의 명령어를 실행하여 에이전트를 Vertex AI Agent Runtime에 성공적으로 배포합니다.
```bash
uv run python agent_runtime.py
```
* 배포가 성공하면 콘솔 창에 **Reasoning Engine Resource Name (Remote Agent Name)**과 **Agent Identity (Federated ID)** 정보가 출력됩니다.

---

## 🔑 Agent Identity 권한 설정 (필수)


```bash
export AGENT_IDENTITY="xxxxxx"

gcloud projects add-iam-policy-binding gcp-sandbox-kwlee \
    --member="principal://$AGENT_IDENTITY" \
    --role="roles/aiplatform.viewer"
gcloud projects add-iam-policy-binding gcp-sandbox-kwlee \
    --member="principal://$AGENT_IDENTITY" \
    --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding gcp-sandbox-kwlee \
    --member="principal://$AGENT_IDENTITY" \
    --role="roles/serviceusage.serviceUsageConsumer"
gcloud projects add-iam-policy-binding gcp-sandbox-kwlee \
    --member="principal://$AGENT_IDENTITY" \
    --role="roles/apptopology.viewer"
gcloud projects add-iam-policy-binding gcp-sandbox-kwlee \
    --member="principal://$AGENT_IDENTITY" \
    --role="roles/agentregistry.viewer"
gcloud projects add-iam-policy-binding gcp-sandbox-kwlee \
    --member="principal://$AGENT_IDENTITY" \
    --role="roles/cloudtrace.user"
gcloud projects add-iam-policy-binding gcp-sandbox-kwlee \
    --member="principal://$AGENT_IDENTITY" \
    --role="roles/logging.viewer"
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
세션 생성 성공 시 전달받은 `SESSION_ID`를 등록하여 날씨와 시간을 조회하는 질문을 에이전트에게 던져봅니다.
```bash
export SESSION_ID="[위 단계에서 발급받은 SESSION_ID]"

curl -s -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  https://us-central1-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}:streamQuery \
  -d '{
    "class_method": "async_stream_query",
    "input": {
      "user_id": "test_user",
      "session_id": "'"${SESSION_ID}"'",
      "message": "'"뉴욕의 현재 날씨와 현재 시간을 알려줘."'"
    }
  }' | jq '.'
```
