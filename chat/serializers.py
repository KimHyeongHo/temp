from rest_framework import serializers
from cards.models import Card, CardBenefit


# 카드 혜택 정보 직렬화
class BenefitSerializer(serializers.ModelSerializer):
    # [설명] 카드 혜택 정보를 JSON으로 변환하는 시리얼라이저
    class Meta:
        model = CardBenefit  # [설명] CardBenefit 모델 기반
        fields = ['benefit_id', 'category_name', 'benefit_rate', 'benefit_limit']  # [설명] 응답에 포함할 필드


# 챗봇 응답용 카드 정보 직렬화
class ChatCardResponseSerializer(serializers.ModelSerializer):
    # [설명] 챗봇이 추천 카드를 응답할 때 사용하는 시리얼라이저
    benefits = BenefitSerializer(many=True, read_only=True)  # [설명] 역참조 관계로 카드의 모든 혜택 정보 포함

    class Meta:
        model = Card  # [설명] Card 모델 기반
        fields = [
            'card_id', 'card_name', 'company', 'card_image_url',  # [설명] 기본 카드 정보
            'annual_fee_domestic', 'annual_fee_overseas',  # [설명] 연회비 정보
            'fee_waiver_rule', 'benefits'  # [설명] 연회비 면제 조건 및 혜택 목록
        ]