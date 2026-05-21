FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# torch 먼저 별도 설치 (CUDA 12.1)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cu121

# 나머지 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENV PYTHONPATH=/app/codeset

CMD ["uvicorn", "codeset.main:app", "--host", "0.0.0.0", "--port", "8000"]