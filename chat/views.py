import uuid
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, serializers
from drf_spectacular.utils import extend_schema, inline_serializer

from .models import ChatRoom, ChatLog
from cards.models import Card
from .serializers import ChatCardResponseSerializer

# 공통 에러 응답 헬퍼 함수
def error_response(message, error_code, reason, status_code):
    return Response({
        "message": message,
        "error_code": error_code,
        "reason": reason
    }, status=status_code)

class MakeChatRoomView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="채팅방 생성 및 세션 연결",
        description="사용자와 챗봇 간의 새로운 채팅 세션을 시작합니다.",
        responses={201: inline_serializer(
            name='ChatRoomCreateResponse',
            fields={
                'type': serializers.CharField(),
                'session_id': serializers.CharField(),
                'message': serializers.CharField(),
                'user_id': serializers.IntegerField(),
                'timestamp': serializers.DateTimeField(),
            }
        )},
        tags=["Chat"]
    )
    def post(self, request):
        try:
            # 1. 채팅방 생성
            auto_title = f"새로운 채팅 {timezone.now().strftime('%m/%d %H:%M')}"
            chat_room = ChatRoom.objects.create(user=request.user, title=auto_title)

            # 2. 세션 ID 생성 (DB의 UUID 또는 PK를 활용하는 것이 안전합니다)
            session_id = f"sess-{chat_room.chatting_room_id}" 

            return Response({
                "type": "CONNECTION_ESTABLISHED",
                "session_id": session_id,
                "message": "챗봇과의 연결이 성공했습니다.",
                "user_id": request.user.user_id,
                "timestamp": timezone.now().isoformat()
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return error_response("채팅방 생성 실패", "DATABASE_ERROR", str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

    def handle_exception(self, exc):
        if isinstance(exc, permissions.NotAuthenticated):
            return error_response("채팅방 생성 실패", "LOGIN_REQUIRED", "로그인이 필요한 서비스입니다.", status.HTTP_401_UNAUTHORIZED)
        return super().handle_exception(exc)


class SendMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="메시지 전송 및 챗봇 응답",
        request=inline_serializer(
            name='SendMessageRequest',
            fields={
                'question': serializers.CharField(),
                'session_id': serializers.CharField()
            }
        ),
        tags=["Chat"]
    )
    def post(self, request):
        question = request.data.get('question')
        session_id = request.data.get('session_id')

        # 1. 유효성 검사
        if not question:
            return error_response("답변 생성 실패", "EMPTY_QUESTION", "질문 내용을 입력해주세요.", status.HTTP_400_BAD_REQUEST)

        # 2. 채팅방 확인
        try:
            # "sess-" 접두어 제거 후 조회
            room_id = session_id.replace("sess-", "") if session_id else None
            room = ChatRoom.objects.get(chatting_room_id=room_id, user=request.user)
        except (ChatRoom.DoesNotExist, ValueError):
            return error_response("답변 생성 실패", "ROOM_NOT_FOUND", "해당 채팅방이 존재하지 않습니다.", status.HTTP_404_NOT_FOUND)

        # 3. 비즈니스 로직 (카드 추천 및 로그 저장)
        try:
            recommended_cards = Card.objects.all()[:1]
            card_data = ChatCardResponseSerializer(recommended_cards, many=True).data
            
            ChatLog.objects.create(
                chatting_room=room,
                question=question,
                answer="추천 카드 정보입니다."
            )

            return Response({
                "type": "CARD_INFO",
                "message_id": f"msg-{uuid.uuid4().hex[:12]}",
                "session_id": session_id,
                "user_id": request.user.user_id,
                "timestamp": timezone.now().isoformat(),
                "data": {"cards": card_data}
            }, status=status.HTTP_200_OK)

        except Exception:
            return error_response("답변 생성 실패", "AI_RESPONSE_TIMEOUT", "챗봇 응답이 지연되고 있습니다.", status.HTTP_504_GATEWAY_TIMEOUT)