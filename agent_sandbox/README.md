# ADK Code Executor Comparison & Guide / ADK 코드 실행기 비교 및 가이드

---

## 🇰🇷 한국어 가이드 (Korean Guide)

ADK(Agent Development Kit) 에이전트에서 분석이나 연산을 위해 코드를 작성하고 실행할 때 선택할 수 있는 **두 가지 코드 실행 방식(Code Execution Options)**에 대한 비교 및 가이드입니다. 

### ⚙️ 코드 실행 방식 개요
에이전트가 코드를 해석하고 실행하는 방법은 다음 두 가지로 분류됩니다.
1. **`AgentEngineSandboxCodeExecutor`**: Vertex AI의 관리형 보안 샌드박스를 활용하는 방식
2. **`BuiltInCodeExecutor`**: Gemini 모델 자체에 내장된 ADK 네이티브 코드 실행 도구를 활용하는 방식 (더 가볍고 통합됨)

---

### 🔍 방식 1: `AgentEngineSandboxCodeExecutor` (Vertex AI 관리형 샌드박스)
Vertex AI Agent Engine 내에 격리된 관리형 샌드박스 환경을 구축하고 이를 ADK 에이전트와 연결하여 사용합니다.

* **핵심 특징:**
  * 🔒 **격리된 보안 환경**: 엔터프라이즈 레벨의 다중 레이어 보안 격리 환경을 제공합니다.
  * 💾 **아티팩트 자동 저장**: 실행 중에 생성된 파일이나 결과물(이미지, CSV 등)이 Google Cloud Storage(GCS)에 자동으로 보관됩니다. (단, 현재 사용자 직접 관리 기능은 제한적이며 추후 지원 예정입니다.)
  * 🔄 **상태 보존(Stateful)**: 세션 내에서 정의한 변수나 데이터 상태가 최대 14일 동안 연속해서 보존됩니다.
  * ⚡ **컴퓨팅 사양 조정**: 샌드박스의 컴퓨팅 리소스(CPU, 메모리 등)를 자유롭게 변경하고 세밀하게 제어할 수 있습니다.
* **적합한 사례**: 강력한 보안 격리가 필요하고, 생성되는 파일 아티팩트를 장기 저장 및 연동해야 하며, 대규모 프로덕션 환경에 최적화된 에이전트 개발 시 적합합니다.

---

### 🔍 방식 2: `BuiltInCodeExecutor` (Gemini 내장 코드 실행기)
Gemini 모델의 Code Execution Extension(코드 실행 확장 프로그램)과 결합된 ADK 자체 네이티브 실행 기능입니다.

* **핵심 특징:**
  * ⚡ **빠르고 간단한 시작**: 별도의 GCS 버킷이나 Vertex AI 샌드박스 리소스를 사전에 프로비저닝할 필요가 없습니다.
  * 🧩 **즉각적인 플러그 앤 플레이**: Gemini API 호출과 동시에 별도 설정 없이 바로 동작합니다.
  * 💡 **Gemini 최적화**: Gemini 모델의 컨텍스트 윈도우 내에서 네이티브하게 작동하여 지연 시간을 최소화합니다.
  * 🔄 **세션 내 임시 상태 유지**: 단일 채팅 세션의 대화 턴 내에서 상태 및 변수를 지속적으로 공유합니다.
  * ⚠️ **참고**: 이 방식은 다른 이벤트 구조(`executable_code` 및 `code_execution_result`)를 사용합니다.
* **적합한 사례**: 빠른 시연(Demo), 튜토리얼, 프로토타이핑 검증 작업이나 파일 저장(Persistence) 및 별도의 자원 튜닝이 필요하지 않는 경량 AI 서비스 구현 시 매우 적합합니다.

---

### 📊 두 방식 한눈에 비교하기

| 비교 항목 | `AgentEngineSandboxCodeExecutor` | `BuiltInCodeExecutor` |
| :--- | :--- | :--- |
| **설정 복잡도** | 보통 (GCS 버킷 및 Agent Runtime 리소스 사전 생성 필요) | 매우 쉬움 (별도 인프라 설정 없음) |
| **지원 모델** | 모든 대형 언어 모델 (Gemini, Claude 등 멀티 모델 지원) | Gemini 모델 제품군 전용 |
| **결과물 보존 (Artifacts)** | GCS 버킷에 자동 보존 (최대 14일 장기 저장) | 인메모리 방식 (대화 세션 종료 시 소멸) |
| **컴퓨팅 자원 제어** | 사용자가 사양(CPU, RAM) 설정 가능 | 제공되는 사양으로 고정 |
| **대화 상태 보존 (State)** | 세션별 최대 14일 동안 상태 및 변수 보존 | 단일 대화 세션의 연속 턴(Turn) 동안 유지 |
| **개발 성숙도** | ✅ Yes (엔터프라이즈 프로덕션 권장) | ⚠️ 빠른 프로토타이핑 / 데모 용도 |
| **입력 (Input)** | 에이전트가 해석할 `Executable code` | 프롬프트(`Prompt`) |
| **출력 (Output)** | 샌드박스로부터의 `Code execution result` | Gemini API를 통한 코드 수행 결과물 |
| **최적 시나리오** | 프로덕션 에이전트, 멀티 모델, 파일 저장이 필요할 때 | 빠른 시연, PoC, Gemini 전용 에이전트 |

---

### 💡 최종 선택 가이드라인

**다음과 같은 경우 `AgentEngineSandboxCodeExecutor`를 사용하십시오:**
- 기업용 프로덕션 환경에 적용하는 에이전트를 개발할 때
- 차트 이미지, 리포트 문서 등 실행 결과 파일들을 GCS에 자동 저장하고 장기간 보존하고 싶을 때
- 코드 실행 시 더 많은 CPU와 메모리 자원을 할당하여 연산 성능을 보강해야 할 때
- 코드 실행 입력 및 출력 구조를 세밀하게 조절해야 할 때

**다음과 같은 경우 `BuiltInCodeExecutor`를 사용하십시오:**
- 아이디어를 빠르게 코드로 구현하고 모델 검증을 시도할 때 (Rapid Prototyping)
- 복잡한 클라우드 아키텍처나 추가 인프라 구축 없이 오직 Gemini API만 활용해 가볍게 구성하고 싶을 때
- 결과물 파일을 저장할 필요 없이 빠른 텍스트 요약 및 경량 연산만 요구될 때
- 데모 및 학습 튜토리얼을 제작할 때

---
---

## 🇺🇸 English Guide (English Guide)

This document compares the **two code execution options** available when writing and executing code for analysis or calculation in ADK (Agent Development Kit) agents.

### ⚙️ Code Execution Overview
The two code execution options are:
1. **`AgentEngineSandboxCodeExecutor`**: Uses Vertex AI's managed, secure sandbox.
2. **`BuiltInCodeExecutor`**: ADK's native code execution capability, integrated with Gemini models (simpler and lightweight).

---

### 🔍 Approach 1: `AgentEngineSandboxCodeExecutor` (Vertex AI Managed Sandbox)
Connects your ADK agent to a managed, isolated sandbox environment created within Vertex AI Agent Engine.

* **Key features:**
  * 🔒 **Isolated Security**: Provides an enterprise-grade secure isolation environment.
  * 💾 **Auto-Save Artifacts**: Output files (images, CSVs, etc.) generated during execution are automatically saved to Google Cloud Storage (GCS). *(Note: User management of these GCS artifacts is currently limited and will be enhanced in future updates).*
  * 🔄 **Stateful Execution**: Variables and data states persist across calls in a session for up to 14 days.
  * ⚡ **Resource Customization**: Offers full control over sandbox configuration (CPU, memory, etc.).
* **Best For**: Production agents that require secure isolation, GCS-backed artifact persistence, scalable performance, and custom resource tuning.

---

### 🔍 Approach 2: `BuiltInCodeExecutor` (Gemini Built-In Code Executor)
ADK's native code execution capability, tightly integrated with Gemini's Code Execution Extension.

* **Key features:**
  * ⚡ **Quick Setup**: No separate GCS bucket or Vertex AI sandbox creation is needed.
  * 🧩 **Plug-and-Play**: Works out-of-the-box as soon as the Gemini API is called.
  * 💡 **Gemini Optimized**: Operates natively within Gemini's context window to minimize latency.
  * 🔄 **Temporary State Retention**: Shares variables and state across the sequential turns of a single model chat session.
  * ⚠️ **Note**: This approach uses a different event structure (`executable_code` and `code_execution_result` parts).
* **Best For**: Quick prototyping, proof-of-concept (PoC) validation, demos, or when resource customization and persistent artifact storage are not required.

---

### 📊 Side-by-Side Comparison

| Feature | `AgentEngineSandboxCodeExecutor` | `BuiltInCodeExecutor` |
| :--- | :--- | :--- |
| **Setup Complexity** | Moderate (requires GCS and Agent Runtime setup) | Simple (no extra infrastructure setup) |
| **Model Support** | Any LLM (Gemini, Claude, etc. - Multi-model support) | Only Gemini model family |
| **Artifact Storage** | Auto-saves to GCS (retains up to 14 days) | In-memory only (deleted when session ends) |
| **Resource Control** | Configurable compute resources (CPU, RAM) | Fixed compute resources |
| **Statefulness** | Stateful (persists up to 14 days per session) | Persists only across turns of a single chat session |
| **Production Ready** | ✅ Yes (enterprise-grade) | ⚠️ Best for prototyping/demos |
| **Input** | `Executable code` | Prompt template (`Prompt`) |
| **Output** | `Code execution result` from sandbox | Code execution output via Gemini API |
| **Best For** | Production agents, multi-model, long-term artifacts | Quick prototypes, PoCs, Gemini-only apps |

---

### 💡 Recommendations

**Choose `AgentEngineSandboxCodeExecutor` when:**
- Building production-ready, enterprise-grade agents.
- You require persistent storage of output files (charts, reports, etc.) in GCS.
- You need to allocate more CPU or memory resources for complex calculations.
- You need precise control over the code execution input and output schemas.

**Choose `BuiltInCodeExecutor` when:**
- Conducting rapid prototyping, experimentation, or PoC validations.
- You want the simplest possible setup using only Gemini models without extra infrastructure.
- You don't need persistent artifact storage and only need text summaries or light calculations.
- Writing tutorials, guides, or developing presentation demos.
