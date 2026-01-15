from django.db import models


# 카테고리 모델
class Category(models.Model):
    # [설명] 지출/구독 등을 분류하는 카테고리 정보 (예: 식비, 교통비, 구독 서비스 등)
    category_id = models.BigAutoField(primary_key=True)  # [설명] PK
    category_name = models.CharField(max_length=45, null=True, blank=True)  # [설명] 카테고리명 (예: "식비", "교통비")
    created_at = models.DateTimeField(auto_now_add=True)  # [설명] 생성 시각
    updated_at = models.DateTimeField(auto_now=True)  # [설명] 수정 시각
    deleted_at = models.DateTimeField(null=True, blank=True)  # [설명] 소프트 삭제용 (null이면 활성 상태)

    class Meta:
        db_table = 'category'  # [설명] 실제 DB 테이블명

    def __str__(self):
        # [설명] admin 등에서 표시될 문자열 포맷
        return f'Category({self.category_id}, {self.category_name})'
