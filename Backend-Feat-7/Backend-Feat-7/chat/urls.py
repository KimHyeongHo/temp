from django.urls import path
from .views import (
    MakeChatRoomView,
    ChatRoomListView,
    ChatRoomDetailView,
    ChatRoomUpdateView,
    SendMessageView
)

app_name = 'chat'

urlpatterns = [
    # 채팅방 관리
    path('rooms/', ChatRoomListView.as_view(), name='chat_room_list'),           # GET: 채팅방 목록
    path('rooms/create/', MakeChatRoomView.as_view(), name='make_chat_room'),    # POST: 채팅방 생성
    path('rooms/<int:room_id>/', ChatRoomDetailView.as_view(), name='chat_room_detail'),  # GET: 상세, DELETE: 삭제
    path('rooms/<int:room_id>/update/', ChatRoomUpdateView.as_view(), name='chat_room_update'),  # PATCH: 제목 수정

    # 메시지
    path('send_message/', SendMessageView.as_view(), name='send_message'),       # POST: 메시지 전송

    # 기존 호환용 (deprecated)
    path('make_room/', MakeChatRoomView.as_view(), name='make_chat_room_legacy'),
]
