import os
import requests
from django.conf import settings


class ChatBotService:
    """OpenAI API를 활용한 챗봇 서비스"""

    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')

    def get_system_prompt(self):
        """카드 추천 서비스에 특화된 시스템 프롬프트"""
        return """당신은 신용카드 추천 전문 AI 어시스턴트입니다.
사용자의 소비 패턴, 생활 스타일, 필요한 혜택을 파악하여 최적의 카드를 추천해주세요.

다음 사항을 고려하여 답변해주세요:
1. 사용자의 주요 소비 카테고리 (식비, 교통, 쇼핑, 온라인 결제 등)
2. 연회비 대비 혜택 가치
3. 포인트/캐시백/할인 등 혜택 유형
4. 부가 서비스 (라운지, 보험 등)

친절하고 전문적으로 답변하되, 간결하게 핵심을 전달해주세요."""

    def generate_response(self, question: str, chat_history: list = None) -> dict:
        """
        AI 응답 생성

        Args:
            question: 사용자 질문
            chat_history: 이전 대화 기록 [(question, answer), ...]

        Returns:
            dict: {'success': bool, 'answer': str, 'error': str}
        """
        if not self.api_key:
            return {
                'success': False,
                'answer': '',
                'error': 'OPENAI_API_KEY가 설정되지 않았습니다.'
            }

        # 메시지 구성
        messages = [{"role": "system", "content": self.get_system_prompt()}]

        # 이전 대화 기록 추가
        if chat_history:
            for q, a in chat_history[-5:]:  # 최근 5개만 컨텍스트로 사용
                messages.append({"role": "user", "content": q})
                messages.append({"role": "assistant", "content": a})

        # 현재 질문 추가
        messages.append({"role": "user", "content": question})

        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": 1000,
                    "temperature": 0.7
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                answer = data['choices'][0]['message']['content']
                return {
                    'success': True,
                    'answer': answer,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'answer': '',
                    'error': f'API 오류: {response.status_code}'
                }

        except requests.Timeout:
            return {
                'success': False,
                'answer': '',
                'error': 'AI 응답 시간이 초과되었습니다.'
            }
        except Exception as e:
            return {
                'success': False,
                'answer': '',
                'error': str(e)
            }

    def generate_fallback_response(self, question: str) -> str:
        """API 키가 없거나 오류 시 폴백 응답"""
        keywords = {
            '추천': '카드 추천을 원하시는군요! 주로 어떤 곳에서 소비를 많이 하시나요? (예: 온라인 쇼핑, 마트, 카페 등)',
            '혜택': '혜택에 대해 궁금하시군요. 캐시백, 포인트 적립, 할인 중 어떤 혜택을 선호하시나요?',
            '연회비': '연회비가 부담되신다면 연회비 무료 카드도 좋은 선택입니다. 연간 사용 금액이 어느 정도 되시나요?',
            '포인트': '포인트 적립 카드를 찾고 계시군요. 적립된 포인트는 주로 어디에 사용하고 싶으신가요?',
        }

        for keyword, response in keywords.items():
            if keyword in question:
                return response

        return '안녕하세요! 카드 추천 서비스입니다. 어떤 카드를 찾고 계신가요? 소비 패턴이나 원하시는 혜택을 말씀해주시면 맞춤 카드를 추천해드릴게요.'


# 싱글톤 인스턴스
chatbot_service = ChatBotService()
