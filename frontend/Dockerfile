FROM node:18-alpine

WORKDIR /app

# 의존성 파일 먼저 복사 후 설치 (캐싱 최적화)
COPY package*.json ./
RUN npm install

# 전체 소스 복사
COPY . .

EXPOSE 3000

CMD ["node", "server.js"]