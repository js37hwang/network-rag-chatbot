import os
import sys
import torch  # GPU 가용성 체크를 위한 라이브러리 추가
import platform  # OS 환경(Win/Darwin)을 감지

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader # pdf 로더
from langchain_textSplitters import RecursiveCharacterTextSplitter # chunking 위해
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_community.embeddings import HuggingFaceBgeEmbeddings # 임베딩 모델 불러오자

# .env 로드
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
load_dotenv()


# -> mysql에 저장하는것으로 바꾸자
## idx/ pdf 파일명/ chunk수/ 파일 저장일시
LOG_FILE_NAME = "indexedFiles.txt"


def selectEmbeddingDevice():
    """
    cuda(gpu) 선택 시 os에 따라 
    Windows/Linux: CUDA(NVIDIA)
    MacOS: MPS(Apple GPU)
    """
    envDevice = os.getenv("EMBEDDING_DEVICE", "cpu").lower()
    currentOS = platform.system() # Windows/ Darwin(Mac)/ Linux
    
    if envDevice == "cuda":

        # Mac
        if currentOS == "Darwin":
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                print("MAC GPU 사용")
                return "mps"
            else:
                print("CPU 사용")
                return "cpu"
                
        # Win/ Linux
        else:
            if torch.cuda.is_available():
                print("NVIDIA GPU 사용")
                return "cuda"
            else:
                print("CPU 사용")
                return "cpu"
                
    print("CPU 사용")
    return "cpu"

# =========================
# 로그 파일 관리 -> 추후 mysql 변경
# =========================
def loadIndexedFiles(log_path):
    if not os.path.exists(log_path):
        return set()
    with open(log_path, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f.readlines() if line.strip())

def saveIndexedFile(log_path, file_name):
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{file_name}\n")


def runIngestion():
    currentDir = os.path.dirname(os.path.abspath(__file__))
    datasetDir = os.path.abspath(os.path.join(currentDir, "../dataset"))
    logFilePath = os.path.join(datasetDir, LOG_FILE_NAME)

    if not os.path.exists(datasetDir):
        print("dataset 폴더 미존재")
        return


    # pdf 파일만 검색
    allFiles = os.listdir(datasetDir)
    pdfFiles = [f for f in allFiles if f.lower().endswith(".pdf")]

    if not pdfFiles:
        print("pdf 파일 미존재")
        return

    print(f"존재 pdf: {pdfFiles}")
    indexedFiles = loadIndexedFiles(logFilePath)

    print(f"이미 등록된 pdf: {list(indexedFiles)}")

    newPdfFiles = [f for f in pdfFiles if f not in indexedFiles]
    if not newPdfFiles:
        print("등록할 pdf 파일 없음")
        return

    print(f"등록할 pdf 파일 {newPdfFiles}")


    # gpu or cpu
    targetDevice = selectEmbeddingDevice()
    

    # 임베딩 모델 가져오기  
    embeddings = HuggingFaceBgeEmbeddings(
        model_name=os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3"),
        model_kwargs={"device": targetDevice},
        encode_kwargs={"normalize_embeddings": True}
    )
    print("임베딩 모델 가져옴")


    # opensearch db 가져오기
    opensearchUrl = os.getenv("OPENSEARCH_ENGEIN_URL", "http://localhost:9200")
    indexName = os.getenv("OPENSEARCH_INDEX_NAME", "cicso_network_index")

    textSplitter = RecursiveCharacterTextSplitter(
        chunk_size=800, # 한단락
        chunk_overlap=100, # 맥락 파악용 중복
        length_function=len
    )

    # 청킹+ opensearch 업로드
    for pdfFile in newPdfFiles:
        fullPdfPath = os.path.join(datasetDir, pdfFile)
        
        try:
            print(f"진행: {pdfFile}")
            loader = PyPDFLoader(fullPdfPath)
            pages = loader.load()
            
            docs = textSplitter.split_documents(pages)
            print(f"chunks: {len(docs)}")

            print(f"OpenSearch 업로드 진행({targetDevice.upper()})")
            OpenSearchVectorSearch.from_documents(
                documents=docs,
                embedding=embeddings,
                opensearch_url=opensearchUrl,
                index_name=indexName,
                bulk_size=10000  
            )

            print(f"적재 성공: {pdfFile}")
            saveIndexedFile(logFilePath, pdfFile)

        except Exception as e:
            print(f"Error: {e}")
            print("다음 파일 진행")

    print("\n인덱싱 종료")

if __name__ == "__main__":
    runIngestion()