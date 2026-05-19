// app.js 전체 교체
const SPRING_API_URL = "http://localhost:8080/api/client/ask";

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

async function sendMessage() {
    const inputEl = document.getElementById("userInput");
    const sendBtnEl = document.getElementById("sendBtn"); // 💡 버튼 엘리먼트 가져오기
    const chatBox = document.getElementById("chatBox");
    const loader = document.getElementById("loaderWrapper");
    
    const question = inputEl.value.trim();
    if (!question) return;

    // 1. 화면에 유저 질문 말풍선 추가
    appendMessage(question, "user-message");
    inputEl.value = ""; // 입력창 비우기

    // ==========================================
    // 💡 [핵심 제어 로직 시작]
    // ==========================================
    
    // 2. ⏳ 채팅창 내부 로딩 말풍선 활성화
    loader.style.display = "block";

    // 3. 🚫 입력 필드 및 전송 버튼 비활성화 (얼리기)
    inputEl.disabled = true;
    sendBtnEl.disabled = true;

    // 말풍선 생성 시 스크롤 최하단 이동
    chatBox.scrollTop = chatBox.scrollHeight;


    try {
        const response = await fetch(SPRING_API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: question })
        });

        if (!response.ok) throw new Error("서버 응답 실패");
        const data = await response.json();

        // 💡 [수정] 통신 성공 시, 먼저 로딩 말풍선을 숨깁니다.
        loader.style.display = "none";

        // 4. AI 답변 및 출처 화면에 추가
        if (data.status === "success") {
            let aiText = data.answer;
            
            if (data.sources && data.sources.length > 0) {
                aiText += "\n\n<div class='source-box'>📚 [참고 문서 내역]<br>";
                data.sources.forEach((src, idx) => {
                    aiText += `• ${src.source} (P.${src.page})<br>`;
                });
                aiText += "</div>";
            }
            appendMessage(aiText, "ai-message");
        } else {
            appendMessage("❌ 답변을 생성하는 중 에러가 발생했습니다.", "ai-message");
        }

    } catch (error) {
        console.error(error);
        // 통신 에러 발생 시에도 로딩창은 숨기고 에러 메시지 출력
        loader.style.display = "none";
        appendMessage("❌ 스프링 부트 서버 연결 실패. 서버 가동 상태를 확인하세요.", "ai-message");
    } finally {
        // ==========================================
        // 💡 [핵심 제어 로직 끝]
        // ==========================================

        // 5. ✅ 답변 도착/에러 발생 상관없이 입력창 및 전송 버튼 활성화 (다시 살리기)
        inputEl.disabled = false;
        sendBtnEl.disabled = false;

        // 최종 답변 도착 후 입력창에 포커스 자동 지정 (바로 다음 질문 입력 가능)
        inputEl.focus();
        
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

function appendMessage(text, className) {
    const chatBox = document.getElementById("chatBox");
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${className}`;
    msgDiv.innerHTML = text;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}