const express = require('express');
const path = require('path');
const app = express();
const PORT = 3000;

// public 폴더 안의 HTML, CSS, JS 파일을 정적 파일로 등록
app.use(express.static(path.join(__dirname, 'public')));

// 사용자가 http://localhost:3000 접속 시 index.html 반환
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
    print("\n🚀 [Node.js Frontend] 서버가 가동되었습니다!");
    print(`🔗 접속 주소: http://localhost:${PORT}\n`);
});