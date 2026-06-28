# Agent Registry 의 MCP 를 연동하는 AI Agent

## 🚀 Agent Runtime 배포를 위한 기본 설정

### 1. 환경 변수 및 관련 API 활성화
배포에 사용할 Google Cloud Project ID를 설정하고 필수 API들을 활성화한 후, 배포 관련 환경 변수를 정의합니다.

```bash
cd ~/agent_platform/graph_workflow
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

export SERVICE_ACCOUNT="graph-workflow-sa"
```

### 2. Cloud Storage 버킷 생성
배포 산출물을 저장할 Google Cloud Storage 버킷을 생성합니다. (이미 사용 중인 버킷이 있다면 이 단계는 건너뛰셔도 됩니다.)

```bash
gcloud storage buckets create ${STAGING_BUCKET_URI} --location=us-central1
```

#### 3. 서비스 계정 생성 및 권한 설정
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
    "roles/aiplatform.user"
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

## 🔍 REST API를 활용한 멀티턴 대화 & HITL 테스트 시나리오

배포 완료 후 반환받은 `REASONING_ENGINE_ID`를 활용하여 REST API (`curl`)를 통해 Human-In-The-Loop(HITL) 프로세스를 포함한 다회차 대화를 수행하고 검증합니다.

### 💡 ADK 2.0 Graph Workflow HITL(Human-In-The-Loop) 핵심 설계 명세 분석
정밀 분석을 통해 도출된 ADK 2.0 Graph Workflow의 HITL 및 Resume 동작 원리는 다음과 같습니다:

1. **독립된 신규 메시지가 아닌 Resume 요청**:
   워크플로우 내에서 `RequestInput`을 발생시켜 일시 정지(Paused) 상태가 된 노드를 재개(Resume)하려면, 완전히 새로운 독립 메시지(`message`)를 보내는 구조가 아닙니다.
2. **`interruptId`와 `resume_inputs` 매핑 필수**:
   이전 노드가 반환했던 고유 ID인 **`interruptId`**를 전달받아, 요청 파라미터 내의 `resume_inputs` 키값에 해당 ID와 사용자의 새로운 입력값을 1:1로 매핑하여 REST API 페이로드로 전송해야만 동기화된 Resume이 최종 성공합니다.
3. **누락 시 문제점 (Rerun 무한 루프)**:
   이를 누락한 채 새로운 메시지만을 보낼 경우, 에이전트는 대화 맥락을 잃고 세션을 계속해서 새로 시작(Rerun)하여 항상 첫 번째 안내 노드(초기화)에만 머물게 되는 치명적인 부작용이 발생합니다.
4. **테스트 스크립트(`test_workflow.py`) 자동화**:
   이러한 메커니즘을 매끄럽게 처리하기 위해, `test_workflow.py`는 실시간 SSE(Server-Sent Events) 스트림 결과에서 `interruptId`를 동적으로 파싱 및 자동 추출하고, 다음 2단계와 3단계 요청의 `resume_inputs` 페이로드에 결합해 동적으로 전달하는 자동화 테스트가 가능하도록 고도화되었습니다.

---

### 0. 공통 환경 변수 정의
테스트를 더 쉽게 진행하기 위해 터미널에 아래 환경 변수들을 먼저 설정해주세요.
```bash
export REASONING_ENGINE_ID="1364888104988573696"
export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")
export LOCATION="us-central1"
```

---

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

### 2️⃣ [Case 1] 일정 추천 서비스 기동 (첫 번째 HITL 대기)
에이전트에게 서비스를 요청하면 에이전트는 필요한 입력 정보(도시, 연령대, 취미 등)가 누락되어 있음을 인지하고, `RequestInput`을 발생시켜 입력을 대기(`PAUSED` 상태)합니다.

```bash
export SESSION_ID="[위 단계에서 발급받은 SESSION_ID]"
export MESSAGE="여행 일정 추천 서비스를 시작해줘."

curl -s -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  https://us-central1-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}:streamQuery \
  -d '{
    "class_method": "async_stream_query",
    "input": {
      "user_id": "test_user",
      "session_id": "'"${SESSION_ID}"'",
      "message": "'"${MESSAGE}"'",
    }
  }' | jq '.'
```

---

### 3️⃣ [Case 2] 선호 정보 전달 및 여행 일정 생성 (두 번째 HITL 대기)
에이전트가 대기하고 있는 상태에서 동일한 세션 ID로 여행 취향 정보를 전달합니다. 에이전트는 이를 Resume하여 5개 이상의 상세 일정이 담긴 `ActivitiesList` 리스트를 출력한 후, 사용자 피드백을 수렴하기 위해 다시 `RequestInput`을 발생시키고 대기(`PAUSED` 상태)합니다.

```bash

export INTERRUPT_ID="[Case 1에서 받은 interruptId]"

curl -s -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  https://us-central1-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}:streamQuery \
  -d '{
    "class_method": "async_stream_query",
    "input": {
      "user_id": "test_user",
      "session_id": "'"${SESSION_ID}"'",
      "message": {
        "role": "user",
        "parts": [
          {
            "function_response": {
              "name": "adk_request_input",
              "id": "'"${INTERRUPT_ID}"'",
              "response": {
                "user response": "도시: 서울, 연령대: 20대, 취미: 맛집 탐방 및 야간 사진 촬영, 좋아했던 관광지: 경복궁 야간 개장"
              }
            }
          }
        ]
      }
    }
  }' | jq '.'
```

---

### 4️⃣ [Case 3] 피드백 루프백 및 일정 반영 업데이트 (완료 및 다음 대기)
사용자가 추천된 일정 중 특정 코스를 다른 코스로 변경해달라는 피드백을 보냅니다. 에이전트는 이를 분석하여 피드백 반영 후 수정된 최종 여행 코스를 갱신하여 반환합니다.


```bash
export INTERRUPT_ID="[Case 2에서 받은 interruptId]"

curl -s -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  https://us-central1-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}:streamQuery \
  -d '{
    "class_method": "async_stream_query",
    "input": {
      "user_id": "test_user",
      "session_id": "'"${SESSION_ID}"'",
      "message": {
        "role": "user",
        "parts": [
          {
            "function_response": {
              "name": "adk_request_input",
              "id": "'"${INTERRUPT_ID}"'",
              "response": {
                "user response": "기본 추천 일정 중 2번 대신, 경복궁 야간 한복 체험 및 인생샷 명소 투어로 일정을 교체하고 상세 설명을 데이트해줘."
              }
            }
          }
        ]
      }
    }
  }' | jq '.'
```


------
### 📝 수정된 부분에 대한 상세 분석

  #### [README.md 추가 내용 요약]

    ### 💡 ADK 2.0 Graph Workflow HITL(Human-In-The-Loop) 핵심 설계 명세 분석
    정밀 분석을 통해 도출된 ADK 2.0 Graph Workflow의 HITL 및 Resume 동작 원리는 다음과 같습니다:

    1. **독립된 신규 메시지가 아닌 Resume 요청**:
       워크플로우 내에서 `RequestInput`을 발생시켜 일시 정지(Paused) 상태가 된 노드를 재개(Resume)하려면, 완전히 새로운 독립 메시지(`message`)를 보내는 구조가 아닙니다.
    2. **`interruptId`와 `resume_inputs` 매핑 필수**:
       이전 노드가 반환했던 고유 ID인 **`interruptId`**를 전달받아, 요청 파라미터 내의 `resume_inputs` 키값에 해당 ID와 사용자의 새로운 입력값을 1:1로 매핑하여 REST API 페이로드로 전송해야만 동기화된 Resume이
  최종 성공합니다.
    3. **누락 시 문제점 (Rerun 무한 루프)**:
       이를 누락한 채 새로운 메시지만을 보낼 경우, 에이전트는 대화 맥락을 잃고 세션을 계속해서 새로 시작(Rerun)하여 항상 첫 번째 안내 노드(초기화)에만 머물게 되는 치명적인 부작용이 발생합니다.
    4. **테스트 스크립트(`test_workflow.py`) 자동화**:
       이러한 메커니즘을 매끄럽게 처리하기 위해, `test_workflow.py`는 실시간 SSE(Server-Sent Events) 스트림 결과에서 `interruptId`를 동적으로 파싱 및 자동 추출하고, 다음 2단계와 3단계 요청의 `resume_inputs`
  페이로드에 결합해 동적으로 전달하는 자동화 테스트가 가능하도록 고도화되었습니다.

  #### [api_test_results.log 추가 내용 요약]

    ================================================================================
    💡 [ADK 2.0 Graph Workflow HITL(Human-In-The-Loop) 핵심 설계 분석 및 테스트 검증 요약]
    ================================================================================

    1. **HITL Resume 핵심 메커니즘**:
       - Graph Workflow 상에서 `RequestInput` 노드를 통해 일시 정지(Paused) 상태가 된 노드를 다시 정상적으로 재개(Resume)하려면 단순 신규 독립 메시지(`message`)를 전달하는 것이 아닙니다.
       - 이전 실행 노드로부터 반환받은 고유 ID인 `interruptId`를 추적하여, 다음 REST API 요청의 `resume_inputs` 파라미터 맵 하위에 `{"[interruptId]": "새로운 사용자 입력값"}` 형태로 명시해 보내야만 세션 상태가
  동기화되며 다음 노드로 재개(Resume)가 진행됩니다.

    2. **미반영 시 부작용 (Rerun 루프)**:
       - 해당 `interruptId` 및 `resume_inputs` 매핑을 누락한 채 일반 메시지만을 전송하면, 에이전트 런타임은 대화 세션의 이전 히스토리를 이어받지 못하고 매 요청마다 세션을 새로 시작(Rerun)하여 첫 번째 안내
  노드에 영원히 머무르는 오작동이 유발됩니다.

    3. **테스트 스크립트(`test_workflow.py`) 개선 결과**:
       - 실시간으로 전달되는 SSE(Server-Sent Events) 스트림 결과 로그로부터 동적으로 `interruptId` 및 `response_schema`의 데이터 타입을 파싱하고 자동 추출하는 엔진을 구현하였습니다.
       - 추출된 동적 `interruptId` 값을 자동으로 다음 Multi-turn API 요청의 `resume_inputs` 구조적 페이로드에 결합하여 REST API를 연쇄 전달함으로써, Case 1 ~ Case 3까지의 여행 일정 수립, 피드백 반영, 변경
  데이터 가공 루프까지 완벽하게 자동 검증을 통과하도록 리팩토링 및 시나리오 테스트를 고도화했습니다.

    ================================================================================
    ──────
  ### 🔍 향후 제안 및 확인 사항

  • 수정된  test_workflow.py  자동화 시나리오가 현재 백그라운드에서 구동 중이라고 하셨는데, 백그라운드 프로세스가 원활히 마무리되면 해당 로그의 하위 디테일도 성공 메시지로 깔끔하게 출력되는지 같이 확인해보시면
  더욱 완벽할 것 같습니다.
  • 혹시 API 호출에서 발생할 수 있는 데이터 타입 유효성 검증 에러( ValidationError  등)가 해결되었는지도 실행 완료 후 확인해 주시기 바랍니다.

  추가적으로 문서 보완이나 다른 리팩토링에 대한 니즈가 있으시면 편히 알려주십시오. 감사합니다!