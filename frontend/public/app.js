function handleKeyPress(event) {
  if (event.key === "Enter") {
    sendMessage();
  }
}

// app.js의 sendMessage 함수 부분만 찾아서 교체해 주세요

async function sendMessage() {
  const inputEl = document.getElementById("userInput");
  const sendBtnEl = document.getElementById("sendBtn");
  const btnTextEl = document.getElementById("btnText"); // 💡 추가
  const btnSpinnerEl = document.getElementById("btnSpinner"); // 💡 추가
  const chatBox = document.getElementById("chatBox");
  const loader = document.getElementById("loaderWrapper");

  const question = inputEl.value.trim();
  if (!question) return;

  // 1. 화면에 유저 질문 말풍선 추가
  appendMessage(question, "user-message");
  inputEl.value = ""; // 입력창 비우기

  // 2. ⏳ 로딩 상태 활성화 (채팅창 내부 말풍선 로딩 오픈)
  loader.style.display = "block";
  inputEl.disabled = true;
  sendBtnEl.disabled = true;

  // 🌟 [핵심 변경] 버튼 내부의 글자를 숨기고 빙글빙글 스피너 개방!
  btnTextEl.style.display = "none";
  btnSpinnerEl.style.display = "block";

  chatBox.scrollTop = chatBox.scrollHeight;

  try {
    const response = await fetch("/api/client/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question }),
    });

    if (!response.ok) throw new Error("서버 응답 실패");
    const data = await response.json();

    loader.style.display = "none";

    if (data.status === "success") {
      let aiText = data.answer;
      if (data.sources && data.sources.length > 0) {
        aiText += "\n\n<div class='source-box'>📚 [참고 문서 내역]<br>";
        data.sources.forEach((src) => {
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
    loader.style.display = "none";
    appendMessage(
      "❌ 서버 연결 실패. 서버 가동 상태를 확인하세요.",
      "ai-message",
    );
  } finally {
    // ==========================================
    // ✅ [복구 시퀀스] 답변 완료 후 원상태 복구
    // ==========================================
    inputEl.disabled = false;
    sendBtnEl.disabled = false;

    // 🌟 버튼 내부의 스피너를 다시 끄고 '전송' 글자 살려내기
    btnTextEl.style.display = "inline";
    btnSpinnerEl.style.display = "none";

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
