import os
import sys
from dotenv import load_dotenv

# .env 로드
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
load_dotenv()

import torch  # GPU 가용성 체크를 위한 라이브러리 추가
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

# =========================
# 설정
# =========================
LOG_FILE_NAME = "indexed_files.txt"

# =========================
# 디바이스(GPU/CPU) 동적 선택 함수
# =========================
def select_embedding_device():
    env_device = os.getenv("EMBEDDING_DEVICE", "cpu").lower()
    
    if env_device == "cuda":
        if torch.cuda.is_available():
            print("🚀 [DEVICE] 시스템에서 NVIDIA GPU가 감지되었습니다. 'CUDA' 가속 모드로 구동합니다.")
            return "cuda"
        else:
            print("⚠️ [WARNING] .env에 cuda가 지정되었으나, 현재 환경에서 GPU 사용이 불가능합니다. 'cpu' 모드로 자동 전환합니다.")
            return "cpu"
    
    print("💻 [DEVICE] 'CPU' 연산 모드로 구동합니다.")
    return "cpu"

# =========================
# 로그 파일 관리
# =========================
def load_indexed_files(log_path):
    if not os.path.exists(log_path):
        return set()
    with open(log_path, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f.readlines() if line.strip())

def save_indexed_file(log_path, file_name):
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{file_name}\n")

# =========================
# 메인 파이프라인
# =========================
def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.abspath(os.path.join(current_dir, "../dataset"))
    log_file_path = os.path.join(dataset_dir, LOG_FILE_NAME)

    print(f"🔄 데이터셋 디렉토리 확인: {dataset_dir}")
    if not os.path.exists(dataset_dir):
        print("❌ dataset 폴더가 존재하지 않습니다.")
        return

    all_files = os.listdir(dataset_dir)
    pdf_files = [f for f in all_files if f.lower().endswith(".pdf")]

    if not pdf_files:
        print("ℹ️ PDF 파일이 없습니다.")
        return

    print(f"📂 발견된 PDF 파일: {pdf_files}")
    indexed_files = load_indexed_files(log_file_path)
    print(f"📜 이미 처리된 파일: {list(indexed_files)}")

    new_pdf_files = [f for f in pdf_files if f not in indexed_files]
    if not new_pdf_files:
        print("✅ 신규 PDF 없음 (이미 모든 파일이 오픈서치에 들어있습니다.)")
        return

    print(f"🚀 신규 적재 시작: {new_pdf_files}")

    # ==========================================
    # 동적 장치 할당 및 임베딩 모델 로드
    # ==========================================
    target_device = select_embedding_device()
    
    print("🔄 고성능 다국어 임베딩 모델(BGE-M3) 로드 중...")
    model_name = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3")
    model_kwargs = {"device": target_device}
    encode_kwargs = {"normalize_embeddings": True}
    
    embeddings = HuggingFaceBgeEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )
    print("✅ 임베딩 모델 초기화 완료")

    # =========================
    # OpenSearch 및 분할기 설정
    # =========================
    opensearch_url = os.getenv("OPENSEARCH_ENGEIN_URL", "http://localhost:9200")
    index_name = os.getenv("OPENSEARCH_INDEX_NAME", "cicso_network_index")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        length_function=len
    )

    # =========================
    # 파일별 인덱싱 수행 루프
    # =========================
    for pdf_file in new_pdf_files:
        full_pdf_path = os.path.join(dataset_dir, pdf_file)
        print(f"\n--- 📄 처리 중: {pdf_file} ---")

        try:
            print(f"   -> 🔄 {pdf_file} 파일 읽는 중... (대용량 파일은 다소 시간이 걸릴 수 있습니다)")
            loader = PyPDFLoader(full_pdf_path)
            pages = loader.load()
            
            docs = text_splitter.split_documents(pages)
            print(f"   -> 🧩 청킹 완료: {len(docs)} chunks")

            # 💡 [핵심 해결책] bulk_size=10000 추가하여 500개 제한 돌파
            print(f"   -> 📡 OpenSearch 업로드 중... (장치: {target_device.upper()})")
            OpenSearchVectorSearch.from_documents(
                documents=docs,
                embedding=embeddings,
                opensearch_url=opensearch_url,
                index_name=index_name,
                bulk_size=10000  # 👈 대량의 청크를 한 번에 쏟아붓도록 옵션 확장
            )

            print(f"   -> 🎉 적재 완료: {pdf_file}")
            save_indexed_file(log_file_path, pdf_file)

        except Exception as e:
            print(f"   -> ❌ 에러 발생: {e}")
            print("   -> 다음 파일로 이동")

    print("\n🏁 모든 인덱싱 과정이 성공적으로 끝났습니다.")

if __name__ == "__main__":
    main()