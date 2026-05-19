import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../codeset")))
from rag import NetMindRAG

def test():
    print("🤖 NetMind RAG 시스템 가동 및 모델 로드 중...")
    rag = NetMindRAG()
    print("✅ 로드 완료!")
    
    test_question = "VLAN 설정하는 방법이나 IP 라우팅 규칙에 대해 매뉴얼 내용을 기반으로 설명해줘."
    print(f"\n💬 사용자 질문: {test_question}")
    print("-" * 60)
    
    # 딕셔너리 형태로 데이터를 받음
    result = rag.query(test_question)
    
    print("\n🤖 [AI 엔지니어 답변]")
    print(result["answer"])
    print("-" * 60)
    
    print("\n📚 [이 답변을 만들기 위해 검사한 오픈서치 매뉴얼 내역]")
    # 중복 출처 제거를 위한 set 활용
    seen_sources = set()
    for idx, src in enumerate(result["sources"], 1):
        source_key = f"{src['source']} (정확히 {src['page']}페이지)"
        if source_key not in seen_sources:
            print(f" 📂 근거 {idx}: {source_key}")
            print(f"   └─ 매뉴얼 실제 문장: {src['content']}")
            seen_sources.add(source_key)
    print("-" * 60)

if __name__ == "__main__":
    test()