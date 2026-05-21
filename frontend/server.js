const express = require("express");
const { createProxyMiddleware } = require("http-proxy-middleware");
const path = require("path");
const app = express();
const PORT = 3000;

// static보다 프록시를 반드시 먼저 등록
app.use(
  "/api",
  createProxyMiddleware({
    target: "http://spring-backend-container:8080",
    changeOrigin: true,
    pathRewrite: { "^/api": "/api" },
    on: {
      proxyReq: (proxyReq, req) => {
        console.log(`[PROXY] ${req.method} ${req.url} -> spring`);
      },
    },
  }),
);

app.use(express.static(path.join(__dirname, "public")));

app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

app.listen(PORT, () => {
  console.log("\n ====== [Node.js Frontend] 서버 가동 ====== ");
  console.log(` ====== 접속 주소: http://localhost:${PORT} ====== \n`);
});
