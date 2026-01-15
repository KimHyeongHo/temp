from django.urls import path
from .views import MakeChatRoomView, SendMessageView  # [설명] 채팅방 생성 및 메시지 전송 뷰 import

app_name = 'chat'  # [설명] URL 네임스페이스 설정

urlpatterns = [
    path('make_room/', MakeChatRoomView.as_view(), name='make_chat_room'),  # [설명] 채팅방 생성 엔드포인트
    path('send_message/', SendMessageView.as_view(), name='send_message'),  # [설명] 메시지 전송 및 챗봇 응답 엔드포인트
]