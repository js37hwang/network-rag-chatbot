# 🔍 Cisco Network RAG 기반 지능형 챗봇 시스템

> **후니의 쉽게 쓴 Cisco network RAG(Retrieval-Augmented Generation) 기반 지능형 챗봇**
> 네트워크 관련 궁금증에 대해 신뢰할 수 있는 출처를 기반으로 답변을 생성하고 실시간으로 중계하는 멀티 컨테이너 아키텍처 시스템입니다.

---

## 🛠 1. 개발 환경 및 기술 스택 (Tech Stack)

본 프로젝트는 서로 다른 환경의 5개 서버/데이터베이스를 Docker로 가상화하여 유기적으로 연동합니다.

| 레이어 | 기술 및 프레임워크 | 버전 | 설명 |
| :--- | :--- | :--- | :--- |
| **Frontend** | Node.js / Express | v18.20.x | 정적 파일 서빙 및 API 프록시 라우팅 |
| **Backend** | Java Spring Framework | v5.3.6 (MVC) | 자바 11 기반 레거시 웹 데이터 중계 브릿지 |
| **AI Engine** | Python / FastAPI | v3.11 / v0.100+ | RAG 기반 문맥 분석 및 임베딩/LLM 추론 |
| **Vector DB** | OpenSearch | v2.11.0 | Cisco 기술 문서 벡터 데이터 임베딩 저장소 |
| **RDBMS** | MySQL | v8.0 | 사용자 데이터 및 기본 관리 스키마 저장소 |

---

## 🏗 2. 시스템 아키텍처 및 흐름 (System Architecture)

```text
[Browser] 
   │ 
   │ (POST /api/client/ask)
   ▼
[Frontend: Node.js (Port 3000)]
   │ 
   │ ► http-proxy-middleware (CORS 방어 및 가로채기)
   ▼ 
   │ (/api -> 포워딩)
   ▼
[Backend: Spring MVC (Port 8181:8080)]
   │ 
   │ ► RestTemplate (데이터 중계 브릿지)
   ▼
[AI Engine: FastAPI (Port 8000)]
   │
   ├─► OpenSearch (벡터 검색을 통한 관련 컨텍스트 추출)
   ├─► MySQL (관계형 데이터 처리)
   │
   └─► 💡 [최종 반환] 환각 없는 출처(Sources) 보장 답변 생성
```


## 🚀 3. 프로젝트 구동 방법 (Installation & Running)
별도의 로컬 개발 환경 세팅(Java, Python 패키지 설치 등) 없이, Docker Compose를 통해 전체 서비스를 한 번에 빌드하고 구동할 수 있습니다.

### 사전 요구사항
Docker Desktop 설치 및 가동 필요

NVIDIA GPU를 사용할 경우, Docker-GPU 가속(NVIDIA Container Toolkit) 설정을 확인하세요.

### 구동 명령어 순서
#### 1. 프로젝트 저장소 클론 및 폴더 이동

```Bash
git clone [https://github.com/js37hwang/network-rag-chatbot.git](https://github.com/js37hwang/network-rag-chatbot.git)
cd network-rag-chatbot
```

#### 2. Docker Compose를 통한 컨테이너 일괄 빌드 및 실행

기존의 빌드 캐시를 초기화하고, Spring의 war 패키징부터 FastAPI 구동까지 한 번에 수행하는 명령어입니다.

```Bash
docker compose down
docker compose up --build -d
```

#### 3. 서비스 가동 확인

모든 컨테이너가 정상적으로 Up 상태인지 확인합니다.

``` Bash
docker compose ps
```

- 서비스별 접속 주소

  - 프론트엔드 웹 UI: http://localhost:3000

  - 스프링 백엔드 API (외부 맵핑): http://localhost:8181

  - AI FastAPI 엔진: http://localhost:8000

## ✨ 4. 프로젝트 핵심 강점 (Key Features)
1. 출처가 보장되는 신뢰성 높은 답변 (Hallucination 방지)

- LLM의 고질적인 문제인 환각 현상을 제어하기 위해 OpenSearch 벡터 DB 내에 적재된 Cisco 공식 문서 규격을 기반으로 조회(Retrieval)하여 정확한 출처 근거를 포함한 답변을 생성합니다.

2. Docker 멀티 컨테이너 기반의 높은 가용성

- 각 서비스 레이어(Node.js, Spring, FastAPI, DB)를 독립된 컨테이너로 완벽히 격리하여 특정 인프라의 장애가 전체 시스템 마비로 이어지지 않도록 구조화했습니다.

3. 환경 변수(ENV) 기반의 유연한 자원 제어 (CPU/GPU)

- docker-compose.yml 파일 내의 환경 변수 및 배포 설정을 통해, 코드의 수정 없이 인프라 사양에 맞추어 GPU(CUDA 디바이스 매핑) 가속 또는 CPU 실행 모드를 유연하게 선택 및 전환할 수 있습니다.
