import uvicorn

if __name__ == "__main__":
    # reload=True 서버 자동 재시작
    uvicorn.run("codeset.main:app", host="0.0.0.0", port=8000, reload=True)