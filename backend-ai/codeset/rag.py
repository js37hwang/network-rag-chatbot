import os
import sys
import torch
import platform  # OS 환경 감지를 위해 유지


from dotenv import load_dotenv
from google import genai
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

from scripts.ingest  import selectEmbeddingDevice






# .env 로드
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
load_dotenv()


class NetMindRAG:
    def __init__(self):
        # gpu or cpu
        targetDevice = selectEmbeddingDevice()


        # 임베딩 모델 로드
        self.embeddings = HuggingFaceBgeEmbeddings(
            model_name=os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3"),
            model_kwargs={"device": targetDevice},
            encode_kwargs={"normalize_embeddings": True}
        )
        
        # OpenSearch 연결
        self.opensearchUrl = os.getenv("OPENSEARCH_ENGEIN_URL", "http://localhost:9200")
        self.indexName = os.getenv("OPENSEARCH_INDEX_NAME", "cicso_network_index")
        
        self.vectorStore = OpenSearchVectorSearch(
            opensearch_url=self.opensearchUrl,
            index_name=self.indexName,
            embedding_function=self.embeddings
        )
        
        # LLM gemini or ollama
        self.llmMode = os.getenv("LLM_MODE", "gemini").lower()
        
        if self.llmMode == "gemini":
            selectedGeminiModel = self._getLatestGeminiModel()
            self.llm = ChatGoogleGenerativeAI(
                model=selectedGeminiModel, 
                temperature=0.2,
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
        elif self.llmMode == "local":
            self.llm = ChatOllama(
                base_url=os.getenv("LOCAL_LLM_URL", "http://localhost:11434"),
                model=os.getenv("LOCAL_MODEL_NAME", "eeve-korean:10.8b"),
                temperature=0.2
            )
        
        # 4. 프롬프트 템플릿 설정
        self.prompt = ChatPromptTemplate.from_template("""
너는 네트워크 및 시스코 시스템 기술 지원을 담당하는 친절하고 전문적인 AI 엔지니어 챗봇이야. 

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


    def _getLatestGeminiModel(self):
        """gemini api"""
        try:
            client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            models = client.models.list()
            availableModels = [m.name.replace("models/", "") for m in models if "generateContent" in getattr(m, "supported_actions", []) and "flash" in m.name.lower()]
            
            return sorted(availableModels, reverse=True)[0] if availableModels else "gemini-1.5-flash"
        except Exception:
            return "gemini-1.5-flash"

    # ==========================================
    # 답변 및 출처 return
    # ==========================================
    def query(self, questionText: str):
        """LLM 답변+ 출처 -> dict"""
        try:
            retriever = self.vectorStore.as_retriever(search_kwargs={"k": 3})
            
            # 출처 작성
            def formatDocs(docs):
                formatted = []
                for doc in docs:
                    source = doc.metadata.get('source', '알수없음').split('\\')[-1]
                    page = doc.metadata.get('page', 0) + 1
                    formatted.append(f"[문서: {source} (P.{page})]\n{doc.page_content}")
                return "\n\n".join(formatted)
            

            # 🌟 랭체인 RunnableParallel 구조 키값 카멜케이스 적용
            ragSetupAndRetrieval = RunnableParallel(
                {"context": retriever | formatDocs, "question": RunnablePassthrough()}
            )
            
            retrievalChain = (
                ragSetupAndRetrieval
                | {
                    "answer": self.prompt | self.llm | StrOutputParser(),
                    "sourceDocuments": lambda x: retriever.invoke(questionText) # 원본 문서 저장 키값 교체
                }
            )
            
            # 체인 실행
            result = retrievalChain.invoke(questionText)
            
            # 깔끔하게 리턴 가공
            sources = []
            for doc in result["sourceDocuments"]:
                cleanSource = doc.metadata.get('source', '알수없음').split('\\')[-1]
                page = doc.metadata.get('page', 0) + 1
                sources.append({"source": cleanSource, "page": page, "content": doc.page_content[:150] + "..."})
                
            return {
                "answer": result["answer"],
                "sources": sources  
            }
            
        except Exception as e:
            return {"answer": f"❌ RAG 엔진 에러: {str(e)}", "sources": []}

if __name__ == "__main__":
    rag = NetMindRAG()
