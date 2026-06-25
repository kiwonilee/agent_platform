# Agent Runtime 연동 (#Agent Identity, #Weather Time Agent, #Agent Runtime)

이 프로젝트는 **날씨 및 시간 조회 도구(Weather & Time Tools)**가 정의된 에이전트를 원격 **Agent Runtime**과 Agent Identity (`types.IdentityType.AGENT_IDENTITY`) 모드로 연동하여 배포하고 서빙하는 환경을 제공합니다.

---

## 🚀 배포 및 권한 설정 가이드

### 1. Agent Runtime에 배포
`agent_platform/agent_runtime/` 디렉터리 내에서 아래 배포 명령을 실행합니다:

```bash
uv run agent_runtime.py
```
* 배포가 성공하면 콘솔 창에 **Reasoning Engine Resource Name (Remote Agent Name)**과 **Agent Identity (Federated ID)** 정보가 출력됩니다.

### 2. Agent Identity에 대한 GCP IAM 권한 할당 (필수)
배포 완료 후, 최종 출력된 에이전트의 고유 Identity가 Gemini AI 모델(Vertex AI)을 호출하고 동작할 수 있도록 필요한 권한을 할당합니다.

> [!WARNING]
> Agent Identity 바인딩 시에는 `user`나 `serviceAccount` 대신, 반드시 **Workload Identity URI 형식(`principal://`)**을 member 인자로 지정해야 오류가 나지 않습니다.

```bash
export PROJECT_ID="[GCP 프로젝트 ID]"
export EFFECTIVE_IDENTITY="[출력된 Agent Identity 값 (e.g. projects/...)]"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="principal://${EFFECTIVE_IDENTITY}" \
    --role="roles/aiplatform.user"
```

---

## 🔍 테스트

API를 직접 호출하기 위한 세션 생성 등의 기본 절차는 최상위 `README.md`의 [공통 API 호출 테스트 가이드](../README.md#🔍-5-공통-api-호출-테스트-가이드)를 참고하세요.

### 테스트 쿼리 예시 (날씨/시간 조회 테스트)

세션이 생성된 후, 발급받은 `SESSION_ID`와 `REASONING_ENGINE_ID`를 환경 변수로 등록하고 아래와 같이 질문을 던져볼 수 있습니다.

```bash
export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")
export MESSAGE="뉴욕의 현재 날씨와 현재 시간을 알려줘."

curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  https://us-central1-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}:streamQuery \
  -d '{
    "class_method": "async_stream_query",
    "input": {
      "user_id": "test_user",
      "session_id": "'"${SESSION_ID}"'",
      "message": "'"${MESSAGE}"'"
    }
  }'
```
