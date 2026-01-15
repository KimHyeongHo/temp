from django.db import models


# 채팅 방
class ChatRoom(models.Model):
    chatting_room_id = models.BigAutoField(primary_key=True)  # [설명] PK
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, db_column='user_id')  # [설명] 채팅방 소유자
    title = models.CharField(max_length=100)  # [설명] 채팅방 제목 (자동 생성 또는 사용자 지정)
    created_at = models.DateTimeField(auto_now_add=True)  # [설명] 생성 시각
    updated_at = models.DateTimeField(auto_now=True)  # [설명] 수정 시각
    deleted_at = models.DateTimeField(null=True, blank=True)  # [설명] 소프트 삭제용 (null이면 활성 상태)

    class Meta:
        db_table = 'chatting_room'  # [설명] 실제 DB 테이블명

    def __str__(self):
        # [설명] admin 등에서 표시될 문자열 포맷
        return f'ChatRoom({self.chatting_room_id}, {self.title})'


# 채팅 기록
class ChatLog(models.Model):
    chat_id = models.BigAutoField(primary_key=True)  # [설명] PK
    chatting_room = models.ForeignKey('ChatRoom', on_delete=models.CASCADE, db_column='chatting_room_id')  # [설명] 소속 채팅방
    question = models.TextField()  # [설명] 사용자가 입력한 질문
    answer = models.TextField()  # [설명] 챗봇이 생성한 답변
    created_at = models.DateTimeField(auto_now_add=True)  # [설명] 생성 시각
    updated_at = models.DateTimeField(auto_now=True)  # [설명] 수정 시각
    deleted_at = models.DateTimeField(null=True, blank=True)  # [설명] 소프트 삭제용 (null이면 활성 상태)

    class Meta:
        db_table = 'chat_logs'  # [설명] 실제 DB 테이블명

    def __str__(self):
        # [설명] admin 등에서 표시될 문자열 포맷
        return f'ChatLog({self.chat_id}, {self.question[:30]}...)'
