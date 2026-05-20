const express = require("express");
const { createProxyMiddleware } = require("http-proxy-middleware");
const path = require("path");
const app = express();
const PORT = 3000;

// /api로 들어온 모든 요청을 도커 내부망 스프링(Tomcat) 서버로 프록시 중계
app.use(
  "/api",
  createProxyMiddleware({
    target: "http://backend-spring:8080", // 도커 내부망이기에 톰캣 포트 8080
    changeOrigin: true,
  }),
);

// public 폴더 안의 HTML, CSS, JS 파일을 정적 파일로 등록
app.use(express.static(path.join(__dirname, "public")));

app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

// 서버 가동
app.listen(PORT, () => {
  console.log("\n ====== [Node.js Frontend] 서버 가동 ====== ");
  console.log(` ====== 접속 주소: http://localhost:${PORT} ====== \n`);
});
