import uvicorn

if __name__ == "__main__":
    # main.py 인스턴스를 8000번 포트로 실행합니다.
    # reload=True 옵션을 주면 코드를 수정할 때마다 서버가 자동으로 재시작되어 개발하기 편합니다.
    uvicorn.run("codeset.main:app", host="0.0.0.0", port=8000, reload=True)