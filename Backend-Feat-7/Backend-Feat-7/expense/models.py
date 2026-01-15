from django.db import models


# 소비 내역
class Expense(models.Model):
    expense_id = models.BigAutoField(primary_key=True)  # [설명] PK
    amount = models.IntegerField()  # [설명] 결제 금액
    merchant_name = models.CharField(max_length=100)  # [설명] 가맹점명
    spent_at = models.DateTimeField(db_index=True)  # [설명] 결제 시각 (날짜 검색 속도 향상용 인덱스)
    benefit_received = models.IntegerField(default=0)  # [설명] 실제로 받은 혜택 금액
    status = models.CharField(  # [설명] 결제 상태 (결제/취소)
        max_length=10,
        choices=[('PAID', '결제됨'), ('CANCELLED', '결제취소')],
        default='PAID',
    )
    user = models.ForeignKey(  # [설명] 결제를 한 사용자
        'users.User',
        on_delete=models.CASCADE,
        db_index=True,  # [설명] 사용자 기준 조회 최적화
    )
    category = models.ForeignKey(  # [설명] 지출 카테고리
        'category.Category',
        on_delete=models.CASCADE,
        db_column='category_id',
    )
    user_card = models.ForeignKey(  # [설명] 사용한 카드 (users_user_cards FK)
        'users.UserCard',
        on_delete=models.CASCADE,
        db_column='user_card_id',
    )
    created_at = models.DateTimeField(auto_now_add=True)  # [설명] 레코드 생성 시각
    updated_at = models.DateTimeField(auto_now=True)  # [설명] 레코드 수정 시각
    deleted_at = models.DateTimeField(null=True, blank=True)  # [설명] 소프트 삭제용

    class Meta:
        db_table = 'expenses'  # [설명] 실제 DB 테이블명

    def __str__(self):
        # [설명] admin 등에서 표시될 문자열
        return f'Expense({self.expense_id}, {self.merchant_name}, {self.amount})'


# 구독 내역
class Subscription(models.Model):
    subs_id = models.BigAutoField(primary_key=True)  # [설명] PK
    service_name = models.CharField(max_length=100)  # [설명] 구독 서비스 이름
    monthly_fee = models.IntegerField()  # [설명] 월 구독료
    next_billing = models.DateField()  # [설명] 다음 결제 예정일

    # Choices (저장할 값, 보여줄 이름)
    status = models.CharField(  # [설명] 구독 상태 (구독중/구독취소)
        max_length=10,
        choices=[('ACTIVE', '구독중'), ('CANCELED', '구독취소')],
        default='ACTIVE',
    )
    user_card = models.ForeignKey(  # [설명] 결제에 사용되는 카드
        'users.UserCard',
        on_delete=models.CASCADE,
        db_column='user_card_id',
    )
    category = models.ForeignKey(  # [설명] 구독 카테고리
        'category.Category',
        on_delete=models.CASCADE,
        db_column='category_id',
    )
    created_at = models.DateTimeField(auto_now_add=True)  # [설명] 레코드 생성 시각
    updated_at = models.DateTimeField(auto_now=True)  # [설명] 레코드 수정 시각
    deleted_at = models.DateTimeField(null=True, blank=True)  # [설명] 소프트 삭제용

    class Meta:
        db_table = 'subscriptions'  # [설명] 실제 DB 테이블명

    def __str__(self):
        # [설명] admin 등에서 표시될 문자열
        return f'Subscription({self.subs_id}, {self.service_name}, {self.status})'