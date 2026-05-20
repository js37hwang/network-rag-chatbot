import os
import sys
import subprocess

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag import NetMindRAG
from scripts.ingest import runIngestion



# 모듈 경로 및 환경 변수 세팅
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(
    title="NetMind AI Support Server",
    description="후니의 시스코 네트워크 기반 RAG 응답을 제공하는 FastAPI 서버입니다.",
    version="1.0.0"
)


# CORS 설정 (환경 변수 기반)
corsOriginsEnv = os.getenv("CORS_ORIGINS", "*")
allowedOrigins = [origin.strip() for origin in corsOriginsEnv.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowedOrigins,  # 💡 도커 컴포즈 환경에 설정된 주소만 정밀 허용
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

# RAG 엔진 인스턴스 전역 생성 
ragEngine = None


@app.on_event("startup")
def startupEvent():
    global ragEngine
    print("\nBE-ai  서버 구동")
    
    try:
        runIngestion()
    except Exception as e:
        print(f"Error: {e}")

    # RAG 엔진 초기화
    ragEngine = NetMindRAG()
    print("RAG Engine 로드 완료\n")



class QuestionRequest(BaseModel):
    question: str

# 질문- 답변 리턴 엔드포인트
@app.post("/api/ai/ask", summary="시스코 매뉴얼 RAG 질의응답 엔드포인트")
def askQuestion(request: QuestionRequest):
    global ragEngine

    if not ragEngine:
        raise HTTPException(status_code=503, detail="RAG 엔진이 아직 준비되지 않았습니다.")
    
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="질문 내용을 입력해 주세요.")
    
    print(f"📥 [API 수신] 스프링 백엔드로부터 질문 도착: {request.question}")
    
    # RAG 파이프라인 구동
    result = ragEngine.query(request.question)
    
    # 스프링이나 프론트엔드가 파싱하기 편하도록 JSON 키값도 카멜케이스 처리
    return {
        "status": "success",
        "answer": result["answer"],
        "sources": result["sources"]
    }

# 기본 엔드포인트
@app.get("/")
def rootCheck():
    return {"status": "running", "message": "NetMind AI 서버가 정상 구동 중입니다."}