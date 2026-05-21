package cisco_network_rag;

import java.util.HashMap;
import java.util.Map;

import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

@RestController
@RequestMapping("/api/client")
// 🌐 브라우저(Vue/React 등)에서 스프링으로 직접 요청을 보낼 때 발생하는 CORS 블로킹을 방지합니다.
@CrossOrigin(origins = "*") 
public class AiBridgeController {

    // 🚀 데이터 중계를 담당하는 컨트롤러 단독 메서드
    @PostMapping("/ask")
    public ResponseEntity<Map<String, Object>> relayQuestionToAiServer(@RequestBody Map<String, String> requestBody) {
        
        // 1. 프론트엔드가 보낸 JSON에서 "question" 문자열 추출
        String userQuestion = requestBody.get("question");
        System.out.println("📥 [Spring 수신] 프론트엔드로부터 전달받은 질문: " + userQuestion);
        
        // 2. 파이썬 FastAPI 서버 주소 및 엔드포인트 설정
        String pythonAiUrl = "http://python-ai-container:8000/api/ai/ask";
        
        // 3. 파이썬 서버로 던질 HTTP Header 및 Body(JSON) 구성
        RestTemplate restTemplate = new RestTemplate();
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON); // 통신 규격을 JSON으로 선언
        
        // 파이썬 FastAPI가 인식할 {'question': '사용자 질문'} 형태의 데이터 생성
        Map<String, String> pythonPayload = new HashMap<String, String>();
        pythonPayload.put("question", userQuestion);
        
        // 헤더와 바디를 하나의 요청 엔티티로 결합
        HttpEntity<Map<String, String>> entityRequest = new HttpEntity<Map<String, String>>(pythonPayload, headers);
        
        try {
            System.out.println("📡 [Spring 토스] 파이썬 AI 서버로 질문 요청 중... (" + pythonAiUrl + ")");
            
            // 4. 파이썬 서버 호출 및 응답 수신 (FastAPI가 주는 success, answer, sources 구조를 그대로 Map으로 받음)
            @SuppressWarnings("unchecked")
            ResponseEntity<Map> aiServerResponse = restTemplate.postForEntity(pythonAiUrl, entityRequest, Map.class);
            
            System.out.println("✅ [Spring 완료] 파이썬 RAG 엔진 응답 수신 성공. 프론트엔드로 전달합니다.");
            
            // 5. 파이썬에서 받아온 데이터 구조 그대로 프론트엔드에 리턴
            return ResponseEntity.status(aiServerResponse.getStatusCode()).body(aiServerResponse.getBody());
            
        } catch (Exception e) {
            System.out.println("❌ [Spring 에러] 파이썬 AI 서버와 통신 중 실패: " + e.getMessage());
            
            // 에러 발생 시 프론트엔드가 인지할 수 있도록 예외 메시지 포맷 리턴
            Map<String, Object> errorResponse = new HashMap<String, Object>();
            errorResponse.put("status", "error");
            errorResponse.put("answer", "죄송합니다. AI 백엔드 서버와의 연결에 실패했습니다.");
            return ResponseEntity.status(500).body(errorResponse);
        }
    }
}