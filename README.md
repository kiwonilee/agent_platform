# [Gemini Enterprise Agent Platform](https://docs.cloud.google.com/gemini-enterprise-agent-platform/overview)

## 🏛️ 1. 아키텍처 및 UV Workspace 구조

### 📦 구성 에이전트 패키지
1. 📊 **`agent_registry`** (`agent-registry`)
   - **역할**: Agent Registry에 등록된 BigQuery MCP를 연동하여 데이터를 분석하는 데이터 사이언티스트 에이전트
   - **핵심 기능**: `Agent Registry` \| `MCP Integration` \| `Agent Runtime` \| `Memory Service` \| `Agent Observability`

2. 🌤️ **`agent_runtime`** (`agent-runtime`)
   - **역할**: 날씨, 시간 등 공통 시스템 도구를 탑재한 기본 실행 에이전트
   - **핵심 기능**: `Agent Runtime` \| `Agent Identity` \| `Memory Service`

3. 🛡️ **`agent_sandbox`** (`agent-sandbox`)
   - **역할**: 생성된 코드를 격리된 환경에서 안전하게 실행할 수 있도록 돕는 샌드박스 에이전트
   - **핵심 기능**: `Agent Sandbox` \| `Agent Runtime` \| `Memory Service` \| `Default Agent SA`

4. 📚 **`skill_registry`** (`skill-registry`)
   - **역할**: Skill Registry에서 적절한 스킬(플레이북)을 검색하여 작업을 수행하는 에이전트
   - **핵심 기능**: `Skill Registry` \| `Agent Runtime` \| `Agent Identity`

> **참고**: 각 에이전트별 특화된 배포 방법 및 요구되는 IAM 권한 설정, 구체적인 테스트 방법은 위 각 폴더의 `README.md`에 자세히 안내되어 있습니다.


---
## 🏛️ 2. 로컬에서 실행

## 🛠️ 1. 로컬 환경에서 실행
```bash
# 최상위 루트 경로에서 실행 (로컬 가상환경 빌드 및 동기화)
uv sync

uv run adk web
```

## 🏛️ 3. 로컬에서 실행

## 🛠️ 1. 환경 초기화 및 환경 변수 설정

1. 환경 변수 파일 설정
   ```bash
   # 최상위 루트 경로에서 실행 (로컬 가상환경 빌드 및 동기화)
   uv sync

   # 1. 환경 변수 정의 (자신의 프로젝트 ID와 GCS 버킷 이름 지정)
   export PROJECT_ID="YOUR_PROJECT_ID"
   export STAGING_BUCKET_URI="gs://YOUR_STAGING_BUCKET_URI"

   # 2. 치환 스크립트 실행 (환경 변수가 자동으로 주입됩니다)
   sed -e "s|your-project-id|${PROJECT_ID}|g" \
       -e "s|your-gcs-bucket|${STAGING_BUCKET_URI}|g" \
       .env.template > .env
   ```
2. 생성된 `.env` 파일을 각 에이전트 디렉토리로 직접 복사
   ```bash
   cp .env agent_registry/.env
   cp .env agent_sandbox/.env
   cp .env skill_registry/.env
   cp .env agent_runtime/.env
   ```


## 🚀 3. Agent Runtime 에 배포


### 전체 배포

```bash
# 전체 에이전트 배포 및 IAM 바인딩 자동 일괄 처리
bash run.sh
```

---

### 개별 배포
각 에이전트 폴더에 진입한 후, 해당 폴더의 `README.md` 파일을 확인

---

## 🔍 4. 공통 API 호출 테스트 가이드

배포된 Reasoning Engine(Agent Runtime)에 API 요청을 보내 테스트를 수행합니다.

### 💡 자동화 테스트 스크립트 사용 (`test.sh`)
이 과정을 편리하게 실행할 수 있도록 `test.sh` 스크립트를 제공합니다.

배포 스크립트(`run.sh`) 실행이 완료되면, 터미널 맨 하단에 배포된 모든 에이전트들의 고유 ID가 `export` 명령어 형태로 일괄 출력됩니다. 해당 출력 블록을 복사해 터미널 세션에 입력(등록)하여 사용합니다.

#### 방법 1: 전체 에이전트 일괄 테스트 (추천)
출력된 환경변수를 등록한 후 바로 아래 명령어를 실행하면, 자동으로 전체 통합 테스트를 순차 수행합니다:
```bash
chmod +x test.sh
./test.sh
```

#### 방법 2: 특정 에이전트 개별 테스트
환경변수로 내보낸 정보를 활용하거나, 혹은 직접 `REASONING_ENGINE_ID`를 매개변수로 명시하여 테스트할 수 있습니다.
```bash
# 등록한 특정 에이전트 테스트 (예: agent_runtime)
./test.sh agent_runtime

# 특정 ID를 직접 지정하여 테스트
./test.sh <REASONING_ENGINE_ID> [agent_registry|agent_sandbox|skill_registry|agent_runtime]
```