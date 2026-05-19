import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 모듈 경로 및 환경 변수 세팅
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from rag import NetMindRAG

# 💡 만약 ingest.py 내부 로직을 함수화했다면 임포트 (예시: def run_ingestion() 구조일 때)
# 여기서는 서버 시작 시 실행될 수 있도록 파일 실행 방식으로 백업 처리해 두었습니다.
import subprocess

app = FastAPI(
    title="NetMind AI Support Server",
    description="후니의 시스코 네트워크 기반 RAG 응답을 제공하는 FastAPI 서버입니다.",
    version="1.0.0"
)

# ==========================================
# 1. 🌐 CORS 설정 (스프링 백엔드 및 브라우저 통신 허용)
# ==========================================
# 현업 및 테스트 환경에서 스프링(주로 8080)이나 프론트엔드와 안전하게 통신하기 위한 설정입니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 과제 환경이므로 전체 허용, 특정하려면 ["http://localhost:8080"] 지정 가능
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, OPTIONS 등 전체 허용
    allow_headers=["*"],
)

# RAG 엔진 인스턴스 전역 생성
rag_engine = None

# ==========================================
# 2. 🚀 서버 시작 시점 (Startup 이벤트) 처리
# ==========================================
@app.on_event("startup")
def startup_event():
    global rag_engine
    print("\n⚡ [FastAPI Startup] 서버 구동 및 초기화 시퀀스를 시작합니다.")
    
    # 🔍 데이터 적재 상태 확인 및 자동 인제스션 실행
    # 매뉴얼 데이터를 담아둔 폴더 위치를 지정합니다. (상황에 맞게 경로 수정 가능)
    pdf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data") 
    
    print(f"📂 매뉴얼 데이터 폴더 확인 중... ({pdf_dir})")
    if os.path.exists(pdf_dir) and any(f.endswith('.pdf') for f in os.listdir(pdf_dir)):
        print("📥 신규 또는 기존 PDF 매뉴얼이 감지되었습니다. 자동 인제스션(데이터 적재)을 확인합니다...")
        try:
            # scripts/ingest.py 스크립트를 서버 기동 시 백그라운드로 안전하게 한 번 실행해 줍니다.
            ingest_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "ingest.py")
            if os.path.exists(ingest_path):
                subprocess.run(["python", ingest_path], check=True)
                print("✅ [Ingestion 완료] 오픈서치 벡터디비 데이터 최신화 성공.")
            else:
                print("⚠️ ingest.py 파일을 찾을 수 없어 자동 적재 과정을 건너뜁니다.")
        except Exception as e:
            print(f"❌ 인제스션 자동 실행 중 에러 발생 (오픈서치에 방이 이미 있다면 무시 가능): {e}")
    else:
        print("💡 감지된 PDF 파일이 없습니다. 기존 벡터 데이터베이스 서고를 그대로 사용합니다.")

    # RAG 엔진 초기화 (BGE-M3 임베딩 및 오픈서치 로드)
    rag_engine = NetMindRAG()
    print("✅ [RAG Engine 로드 완료] 이제 질문을 받을 준비가 되었습니다.\n")


# ==========================================
# 3. 📝 API 데이터 규격 정의 (DTO)
# ==========================================
class QuestionRequest(BaseModel):
    question: str

# ==========================================
# 4. 🖨️ 질문 처리 엔드포인트 (POST /api/ai/ask)
# ==========================================
@app.post("/api/ai/ask", summary="시스코 매뉴얼 RAG 질의응답 엔드포인트")
def ask_question(request: QuestionRequest):
    global rag_engine
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG 엔진이 아직 준비되지 않았습니다.")
    
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="질문 내용을 입력해 주세요.")
    
    print(f"📥 [API 수신] 스프링 백엔드로부터 질문 도착: {request.question}")
    
    # RAG 파이프라인 구동 (답변과 출처 내역이 포함된 딕셔너리 반환)
    result = rag_engine.query(request.question)
    
    # 스프링 부트나 프론트엔드가 파싱하기 가장 좋은 JSON 구조로 리턴합니다.
    return {
        "status": "success",
        "answer": result["answer"],
        "sources": result["sources"]
    }

# 기본 헬스체크용 엔드포인트
@app.get("/")
def root_check():
    return {"status": "running", "message": "NetMind AI 서버가 정상 구동 중입니다."}