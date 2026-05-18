import os
import sys
from dotenv import load_dotenv

# .env 로드
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
load_dotenv()

import torch
from google import genai
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

class NetMindRAG:
    def __init__(self):
        # 1. 임베딩 모델 로드
        env_device = os.getenv("EMBEDDING_DEVICE", "cpu").lower()
        target_device = "cuda" if (env_device == "cuda" and torch.cuda.is_available()) else "cpu"
        
        model_name = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3")
        self.embeddings = HuggingFaceBgeEmbeddings(
            model_name=model_name,
            model_kwargs={"device": target_device},
            encode_kwargs={"normalize_embeddings": True}
        )
        
        # 2. OpenSearch 연결
        self.opensearch_url = os.getenv("OPENSEARCH_ENGEIN_URL", "http://localhost:9200")
        self.index_name = os.getenv("OPENSEARCH_INDEX_NAME", "cicso_network_index")
        
        self.vector_store = OpenSearchVectorSearch(
            opensearch_url=self.opensearch_url,
            index_name=self.index_name,
            embedding_function=self.embeddings
        )
        
        # 3. LLM 모드 동적 분기
        self.llm_mode = os.getenv("LLM_MODE", "gemini").lower()
        
        if self.llm_mode == "gemini":
            selected_gemini_model = self._get_latest_gemini_model()
            self.llm = ChatGoogleGenerativeAI(
                model=selected_gemini_model, 
                temperature=0.2,
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
        elif self.llm_mode == "local":
            self.llm = ChatOllama(
                base_url=os.getenv("LOCAL_LLM_URL", "http://localhost:11434"),
                model=os.getenv("LOCAL_MODEL_NAME", "eeve-korean:10.8b"),
                temperature=0.2
            )
        
        # 4. 프롬프트 템플릿 설정
        self.prompt = ChatPromptTemplate.from_template("""
너는 네트워크 및 시스코 시스템 기술 지원을 담당하는 친절하고 전문적인 AI 엔지니어 'NetMind 봇'이야. 

[답변 가이드라인]
1. 반드시 아래 제공된 [참고 문서 context]의 내용만을 바탕으로 사용자의 질문에 답변해줘.
2. 문장의 끝은 항상 "~입니다.", "~하셔야 합니다."와 같이 정중하고 확신에 찬 엔지니어의 어조를 사용해줘.
3. 중요하거나 가독성이 필요한 부분은 적절히 줄바꿈과 글머리 기호(*)를 사용해서 가독성 있게 정리해줘.
4. 만약 참고 문서에 질문과 관련된 정보가 전혀 없다면, 말을 지어내지 말고 "죄송합니다. 제공된 매뉴얼에서 관련 기술 정보를 찾을 수 없습니다."라고 정중하게 답변해줘.

[참고 문서 context]
{context}

[사용자 질문]
{question}

[엔지니어 답변]:
""")

    # ==========================================
    # 동적 LLM 모델 로드
    # ==========================================
    def _get_latest_gemini_model(self):
        try:
            client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            models = client.models.list()
            available_models = [m.name.replace("models/", "") for m in models if "generateContent" in getattr(m, "supported_actions", []) and "flash" in m.name.lower()]
            return sorted(available_models, reverse=True)[0] if available_models else "gemini-1.5-flash"
        except Exception:
            return "gemini-1.5-flash"

    # ==========================================
    # 답변 및 출처 return
    # ==========================================
    def query(self, question_text: str):
        """질문을 던지면 오픈서치 검색 결과(출처)와 LLM 답변을 동시에 딕셔너리로 반환합니다."""
        try:
            retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
            
            # 검색된 문서 조각들을 하나의 문자열로 포맷팅하는 함수
            def format_docs(docs):
                formatted = []
                for doc in docs:
                    source = doc.metadata.get('source', '알수없음').split('\\')[-1]
                    page = doc.metadata.get('page', 0) + 1
                    formatted.append(f"[문서: {source} (P.{page})]\n{doc.page_content}")
                return "\n\n".join(formatted)
            
            # 🌟 핵심: 랭체인 RunnableParallel 구조 적용
            # 'source_documents'에는 검색된 생 원본 배열을 남겨두고, 
            # 'answer'에는 기존 RAG 파이프라인을 돌려 대답을 만듭니다.
            rag_setup_and_retrieval = RunnableParallel(
                {"context": retriever | format_docs, "question": RunnablePassthrough()}
            )
            
            retrieval_chain = (
                rag_setup_and_retrieval
                | {
                    "answer": self.prompt | self.llm | StrOutputParser(),
                    "source_documents": lambda x: retriever.invoke(question_text) # 원본 문서 따로 저장
                }
            )
            
            # 체인 실행
            result = retrieval_chain.invoke(question_text)
            
            # 깔끔하게 리턴 가공
            sources = []
            for doc in result["source_documents"]:
                clean_source = doc.metadata.get('source', '알수없음').split('\\')[-1]
                page = doc.metadata.get('page', 0) + 1
                sources.append({"source": clean_source, "page": page, "content": doc.page_content[:150] + "..."})
                
            return {
                "answer": result["answer"],
                "sources": sources  # 👈 어느 파일의 몇 페이지를 참고했는지 리스트 제공!
            }
            
        except Exception as e:
            return {"answer": f"❌ RAG 엔진 에러: {str(e)}", "sources": []}