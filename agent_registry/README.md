# Agent Registry 의 MCP 를 연동하는 AI Agent

## 🚀 Agent Runtime 배포를 위한 기본 설정

### 1. 환경 변수 및 관련 API 활성화
배포에 사용할 Google Cloud Project ID를 설정하고 필수 API들을 활성화한 후, 배포 관련 환경 변수를 정의합니다.

```bash
cd ~/agent_platform/agent_registry
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
export SERVICE_ACCOUNT="agent-registry-sa"
```

### 2. Cloud Storage 버킷 생성
배포 산출물을 저장할 Google Cloud Storage 버킷을 생성합니다. (이미 사용 중인 버킷이 있다면 이 단계는 건너뛰셔도 됩니다.)

```bash
gcloud storage buckets create ${STAGING_BUCKET_URI} --location=us-central1
```

### 3. 서비스 계정 생성 및 권한 설정
```bash
# 서비스 계정 이메일 주소 정의 (자동 매칭)
export SA_EMAIL="${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"

# 서비스 계정 생성
gcloud iam service-accounts create ${SERVICE_ACCOUNT} \
    --description="Service account for Agent Registry deployment" \
    --display-name="agent-registry-sa"

# 필요한 IAM 역할 목록
ROLES=(
    "roles/cloudtrace.user"
    "roles/cloudtrace.agent"
    "roles/logging.viewer"
    "roles/logging.logWriter"
    "roles/storage.objectAdmin"
    "roles/aiplatform.user"    
    "roles/agentregistry.viewer"
    "roles/mcp.toolUser"
)

# 반복문을 통해 권한 일괄 부여
for ROLE in "${ROLES[@]}"; do
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="${ROLE}"
done
```

### 4. `.env` 파일 생성 및 서비스 계정 추가
부모 디렉토리의 환경 변수 템플릿(`.env.template`)을 참조하여 프로젝트 정보를 치환한 로컬 `.env` 파일을 생성하고, 배포에 사용할 서비스 계정 이메일 변수를 안전하게 등록합니다.

```bash
# 1. 환경 변수 템플릿을 치환하여 로컬 .env 생성 (agent_registry 디렉토리 내부에서 실행)
sed -e "s|your-project-id|${PROJECT_ID}|g" \
    -e "s|your-gcs-bucket|${STAGING_BUCKET_URI}|g" \
    ../.env.template > .env

# 2. 서비스 계정 이메일을 배포 환경 변수로 추가 등록
echo "SERVICE_ACCOUNT=${SA_EMAIL}" >> .env
```

### 5. `.env` 파일에 MCP 서버 정보 등록
에이전트가 연동할 Google Cloud Logging MCP 서버를 `gcloud` 명령어로 검색하여 리소스 이름을 `.env` 파일에 자동으로 등록합니다.

```bash
# 1. logging.googleapis.com MCP 서버의 ID를 조회하여 .env 파일에 등록합니다.
export MCP_SERVER_NAME=$(gcloud alpha agent-registry mcp-servers list \
    --location=global \
    --filter="displayName:logging.googleapis.com" \
    --format="value(name.basename())")

echo "MCP_SERVER_NAME=\"mcpServers/${MCP_SERVER_NAME}\"" >> .env

# 2. 최종 설정이 정상적으로 반영되었는지 확인
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
세션 생성 성공 시 전달받은 `SESSION_ID`를 등록하여 BigQuery 데이터를 수집/조회하는 질문을 에이전트에게 던져봅니다.
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
      "message": "최근 발생한 에러로그 5개를 분석해줘."
    }
  }'
```