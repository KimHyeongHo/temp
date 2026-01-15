from django.db import models


# 카드 정보 모델
class Card(models.Model):
    card_id = models.BigAutoField(primary_key=True)  # [설명] PK
    card_name = models.CharField(max_length=100)  # [설명] 카드 이름
    company = models.CharField(max_length=50)  # [설명] 카드 발급사 (예: "신한카드", "KB국민카드")
    card_image_url = models.CharField(max_length=500, null=True, blank=True)  # [설명] 카드 이미지 URL
    annual_fee_domestic = models.IntegerField(default=0)  # [설명] 국내 연회비
    annual_fee_overseas = models.IntegerField(default=0)  # [설명] 해외 연회비
    fee_waiver_rule = models.CharField(max_length=500, null=True, blank=True)  # [설명] 연회비 면제 조건 텍스트
    baseline_requirements_text = models.CharField(max_length=500, null=True, blank=True)  # [설명] 기본 요구사항 텍스트 (예: "연소득 3000만원 이상")
    benefit_cap_summary = models.CharField(max_length=500, null=True, blank=True)  # [설명] 혜택 요약 필드 (예: "연간 최대 100만원 혜택")
    created_at = models.DateTimeField(auto_now_add=True)  # [설명] 생성일
    updated_at = models.DateTimeField(auto_now=True)  # [설명] 수정일
    deleted_at = models.DateTimeField(null=True, blank=True)  # [설명] 소프트 삭제용 (null이면 활성 상태)

    class Meta:
        db_table = 'cards'  # [설명] 실제 DB 테이블명

    def __str__(self):
        # [설명] admin 등에서 표시될 문자열 포맷
        return f'Card({self.card_id}, {self.card_name})'


# 카드 혜택 모델
class CardBenefit(models.Model):
    # [설명] 카드별 카테고리별 혜택 정보 (예: 식비 5% 할인, 교통비 3% 할인)
    benefit_id = models.BigAutoField(primary_key=True)  # [설명] PK
    card = models.ForeignKey('Card', on_delete=models.CASCADE, db_column='card_id')  # [설명] 소속 카드
    category = models.ForeignKey('category.Category', on_delete=models.CASCADE, db_column='category_id')  # [설명] 혜택이 적용되는 카테고리
    benefit_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # [설명] 혜택율 (예: 1.50 = 1.5%)
    benefit_limit = models.IntegerField(null=True, blank=True)  # [설명] 혜택 한도 (예: 월 10만원)
    created_at = models.DateTimeField(auto_now_add=True)  # [설명] 생성일
    updated_at = models.DateTimeField(auto_now=True)  # [설명] 수정일
    deleted_at = models.DateTimeField(null=True, blank=True)  # [설명] 소프트 삭제용 (null이면 활성 상태)

    class Meta:
        db_table = 'card_benefits'  # [설명] 실제 DB 테이블명

    def __str__(self):
        # [설명] admin 등에서 표시될 문자열 포맷
        return f'CardBenefit({self.benefit_id}, {self.card.card_name}, {self.benefit_rate}%)'