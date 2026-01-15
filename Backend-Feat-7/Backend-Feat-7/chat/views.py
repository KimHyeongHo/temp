import uuid
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, serializers
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiParameter

from .models import ChatRoom, ChatLog
from .services import chatbot_service
from cards.models import Card
from .serializers import ChatCardResponseSerializer


def error_response(message, error_code, reason, status_code):
    """공통 에러 응답 헬퍼 함수"""
    return Response({
        "message": message,
        "error_code": error_code,
        "reason": reason
    }, status=status_code)


class MakeChatRoomView(APIView):
    """채팅방 생성 API"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="채팅방 생성",
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
            auto_title = f"새로운 채팅 {timezone.now().strftime('%m/%d %H:%M')}"
            chat_room = ChatRoom.objects.create(user=request.user, title=auto_title)
            session_id = f"sess-{chat_room.chatting_room_id}"

            return Response({
                "type": "CONNECTION_ESTABLISHED",
                "session_id": session_id,
                "chatting_room_id": chat_room.chatting_room_id,
                "message": "챗봇과의 연결이 성공했습니다.",
                "user_id": request.user.user_id,
                "timestamp": timezone.now().isoformat()
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return error_response("채팅방 생성 실패", "DATABASE_ERROR", str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatRoomListView(APIView):
    """채팅방 목록 조회 API"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="채팅방 목록 조회",
        description="사용자의 모든 채팅방 목록을 조회합니다.",
        responses={200: inline_serializer(
            name='ChatRoomListResponse',
            fields={
                'chatting_rooms': serializers.ListField(child=serializers.DictField()),
                'total_count': serializers.IntegerField(),
            }
        )},
        tags=["Chat"]
    )
    def get(self, request):
        try:
            chat_rooms = ChatRoom.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).order_by('-updated_at')

            rooms_data = [{
                'chatting_room_id': room.chatting_room_id,
                'session_id': f"sess-{room.chatting_room_id}",
                'title': room.title,
                'created_at': room.created_at.isoformat(),
                'updated_at': room.updated_at.isoformat(),
                'last_message': self._get_last_message(room)
            } for room in chat_rooms]

            return Response({
                'chatting_rooms': rooms_data,
                'total_count': len(rooms_data)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return error_response("채팅방 목록 조회 실패", "DATABASE_ERROR", str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_last_message(self, room):
        """마지막 메시지 가져오기"""
        last_log = ChatLog.objects.filter(
            chatting_room=room,
            deleted_at__isnull=True
        ).order_by('-created_at').first()

        if last_log:
            return {
                'question': last_log.question[:50] + '...' if len(last_log.question) > 50 else last_log.question,
                'created_at': last_log.created_at.isoformat()
            }
        return None


class ChatRoomDetailView(APIView):
    """채팅방 상세 조회 및 삭제 API"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="채팅방 상세 조회",
        description="채팅방의 상세 정보와 채팅 기록을 조회합니다.",
        parameters=[
            OpenApiParameter(name='room_id', type=int, location=OpenApiParameter.PATH, description='채팅방 ID')
        ],
        responses={200: inline_serializer(
            name='ChatRoomDetailResponse',
            fields={
                'chatting_room_id': serializers.IntegerField(),
                'title': serializers.CharField(),
                'created_at': serializers.DateTimeField(),
                'chat_logs': serializers.ListField(child=serializers.DictField()),
            }
        )},
        tags=["Chat"]
    )
    def get(self, request, room_id):
        try:
            room = ChatRoom.objects.get(
                chatting_room_id=room_id,
                user=request.user,
                deleted_at__isnull=True
            )
        except ChatRoom.DoesNotExist:
            return error_response("채팅방 조회 실패", "ROOM_NOT_FOUND", "해당 채팅방이 존재하지 않습니다.", status.HTTP_404_NOT_FOUND)

        chat_logs = ChatLog.objects.filter(
            chatting_room=room,
            deleted_at__isnull=True
        ).order_by('created_at')

        logs_data = [{
            'chat_id': log.chat_id,
            'question': log.question,
            'answer': log.answer,
            'created_at': log.created_at.isoformat()
        } for log in chat_logs]

        return Response({
            'chatting_room_id': room.chatting_room_id,
            'session_id': f"sess-{room.chatting_room_id}",
            'title': room.title,
            'created_at': room.created_at.isoformat(),
            'updated_at': room.updated_at.isoformat(),
            'chat_logs': logs_data,
            'total_messages': len(logs_data)
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="채팅방 삭제",
        description="채팅방을 삭제합니다. (소프트 삭제)",
        parameters=[
            OpenApiParameter(name='room_id', type=int, location=OpenApiParameter.PATH, description='채팅방 ID')
        ],
        responses={200: inline_serializer(
            name='ChatRoomDeleteResponse',
            fields={
                'message': serializers.CharField(),
            }
        )},
        tags=["Chat"]
    )
    def delete(self, request, room_id):
        try:
            room = ChatRoom.objects.get(
                chatting_room_id=room_id,
                user=request.user,
                deleted_at__isnull=True
            )
        except ChatRoom.DoesNotExist:
            return error_response("채팅방 삭제 실패", "ROOM_NOT_FOUND", "해당 채팅방이 존재하지 않습니다.", status.HTTP_404_NOT_FOUND)

        # 소프트 삭제
        room.deleted_at = timezone.now()
        room.save()

        # 채팅 기록도 소프트 삭제
        ChatLog.objects.filter(chatting_room=room).update(deleted_at=timezone.now())

        return Response({
            'message': '채팅방이 삭제되었습니다.',
            'chatting_room_id': room_id
        }, status=status.HTTP_200_OK)


class ChatRoomUpdateView(APIView):
    """채팅방 제목 수정 API"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="채팅방 제목 수정",
        description="채팅방의 제목을 수정합니다.",
        request=inline_serializer(
            name='ChatRoomUpdateRequest',
            fields={
                'title': serializers.CharField()
            }
        ),
        responses={200: inline_serializer(
            name='ChatRoomUpdateResponse',
            fields={
                'message': serializers.CharField(),
                'chatting_room_id': serializers.IntegerField(),
                'title': serializers.CharField(),
            }
        )},
        tags=["Chat"]
    )
    def patch(self, request, room_id):
        try:
            room = ChatRoom.objects.get(
                chatting_room_id=room_id,
                user=request.user,
                deleted_at__isnull=True
            )
        except ChatRoom.DoesNotExist:
            return error_response("채팅방 수정 실패", "ROOM_NOT_FOUND", "해당 채팅방이 존재하지 않습니다.", status.HTTP_404_NOT_FOUND)

        new_title = request.data.get('title')
        if not new_title:
            return error_response("채팅방 수정 실패", "INVALID_INPUT", "제목을 입력해주세요.", status.HTTP_400_BAD_REQUEST)

        room.title = new_title
        room.save()

        return Response({
            'message': '채팅방 제목이 수정되었습니다.',
            'chatting_room_id': room.chatting_room_id,
            'title': room.title
        }, status=status.HTTP_200_OK)


class SendMessageView(APIView):
    """메시지 전송 및 AI 응답 API"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="메시지 전송 및 AI 응답",
        description="사용자 메시지를 전송하고 AI 챗봇의 응답을 받습니다.",
        request=inline_serializer(
            name='SendMessageRequest',
            fields={
                'question': serializers.CharField(),
                'session_id': serializers.CharField()
            }
        ),
        responses={200: inline_serializer(
            name='SendMessageResponse',
            fields={
                'type': serializers.CharField(),
                'message_id': serializers.CharField(),
                'session_id': serializers.CharField(),
                'question': serializers.CharField(),
                'answer': serializers.CharField(),
                'timestamp': serializers.DateTimeField(),
            }
        )},
        tags=["Chat"]
    )
    def post(self, request):
        question = request.data.get('question')
        session_id = request.data.get('session_id')

        # 1. 유효성 검사
        if not question:
            return error_response("답변 생성 실패", "EMPTY_QUESTION", "질문 내용을 입력해주세요.", status.HTTP_400_BAD_REQUEST)

        if not session_id:
            return error_response("답변 생성 실패", "EMPTY_SESSION", "세션 ID를 입력해주세요.", status.HTTP_400_BAD_REQUEST)

        # 2. 채팅방 확인
        try:
            room_id = session_id.replace("sess-", "") if session_id else None
            room = ChatRoom.objects.get(
                chatting_room_id=room_id,
                user=request.user,
                deleted_at__isnull=True
            )
        except (ChatRoom.DoesNotExist, ValueError):
            return error_response("답변 생성 실패", "ROOM_NOT_FOUND", "해당 채팅방이 존재하지 않습니다.", status.HTTP_404_NOT_FOUND)

        # 3. 이전 대화 기록 가져오기
        chat_history = list(ChatLog.objects.filter(
            chatting_room=room,
            deleted_at__isnull=True
        ).order_by('-created_at')[:5].values_list('question', 'answer'))
        chat_history.reverse()

        # 4. AI 응답 생성
        ai_result = chatbot_service.generate_response(question, chat_history)

        if ai_result['success']:
            answer = ai_result['answer']
        else:
            # 폴백 응답 사용
            answer = chatbot_service.generate_fallback_response(question)

        # 5. 채팅 기록 저장
        chat_log = ChatLog.objects.create(
            chatting_room=room,
            question=question,
            answer=answer
        )

        # 6. 채팅방 updated_at 갱신
        room.save()

        # 7. 관련 카드 추천 (옵션)
        recommended_cards = self._get_recommended_cards(question)
        card_data = ChatCardResponseSerializer(recommended_cards, many=True).data if recommended_cards else []

        return Response({
            "type": "AI_RESPONSE",
            "message_id": f"msg-{chat_log.chat_id}",
            "session_id": session_id,
            "user_id": request.user.user_id,
            "question": question,
            "answer": answer,
            "timestamp": timezone.now().isoformat(),
            "recommended_cards": card_data
        }, status=status.HTTP_200_OK)

    def _get_recommended_cards(self, question):
        """질문에 기반한 카드 추천 (간단한 키워드 매칭)"""
        keywords_to_category = {
            '쇼핑': ['쇼핑', '온라인'],
            '마트': ['마트', '대형마트'],
            '카페': ['카페', '커피'],
            '주유': ['주유', '자동차'],
            '여행': ['여행', '항공'],
        }

        for keyword, categories in keywords_to_category.items():
            if keyword in question:
                return Card.objects.filter(
                    category__category_name__in=categories
                )[:3]

        return Card.objects.all()[:2]
