# serializers.py
from rest_framework import serializers
from .models import Card, CardBenefit

# 카드 시리얼라이저
class CardSerializer(serializers.ModelSerializer):
    image = serializers.ReadOnlyField(source='card_image_url') # 카드 이미지 URL 매핑
    
    class Meta:
        model = Card 
        fields = ['card_id', 'card_name', 'card_number', 'image'] # card_number 필드 추가

# 추천 카드 시리얼라이저
class RecommendedCardSerializer(serializers.ModelSerializer):
    image = serializers.ReadOnlyField(source='card_image_url') # 카드 이미지 URL 매핑
    benefit_summary = serializers.ReadOnlyField(source='benefit_cap_summary') # 혜택 요약 매핑
    annual_fee = serializers.ReadOnlyField(source='annual_fee_domestic') # 국내 연회비 매핑
    annual_fee_international = serializers.ReadOnlyField(source='annual_fee_overseas') # 해외 연회비 매핑

    class Meta:
        model = Card
        fields = ['card_id', 'card_name', 'annual_fee', 'annual_fee_international', 
                  'company', 'image', 'benefit_summary']
        
# 카드 등록 시리얼라이저

class CardRegisterSerializer(serializers.ModelSerializer):
    cardId = serializers.IntegerField(source='card_id', read_only=True)
    cardName = serializers.CharField(source='card_name', write_only=True)
    displayCardName = serializers.CharField(source='card_name', read_only=True)
    registeredAt = serializers.DateTimeField(source='created_at', format="%Y-%m-%dT%H:%M:%S", read_only=True)
    
    # [중요] JSON의 'benefits' 리스트를 받기 위해 명시적으로 선언
    benefits = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = Card
        fields = [
            'cardId','cardName', 'displayCardName', 'registeredAt',
            'company', 'card_image_url', 'annual_fee_domestic', 
            'annual_fee_overseas', 'fee_waiver_rule', 
            'baseline_requirements_text', 'benefit_cap_summary', 'card_number',
            'benefits' 
        ]
        extra_kwargs = {
            'card_name': {'write_only': True},
            'company': {'write_only': True},
            'card_image_url': {'write_only': True},
            'annual_fee_domestic': {'write_only': True},
            'annual_fee_overseas': {'write_only': True},
            'fee_waiver_rule': {'write_only': True},
            'baseline_requirements_text': {'write_only': True},
            'benefit_cap_summary': {'write_only': True},
            'card_number': {'write_only': True},
        }

    # [수정] create 메서드를 클래스 안(Meta와 같은 레벨)으로 이동
    def create(self, validated_data):
        # 1. Card 모델에 없는 'benefits'를 먼저 제거(pop)하여 에러 방지
        benefits_data = validated_data.pop('benefits', [])
        
        # 2. 유저 정보 할당
        user = self.context['request'].user
        validated_data['user'] = user
        
        # 3. 깨끗해진 데이터로 Card 객체 생성
        card = Card.objects.create(**validated_data)
        
        # 4. 혜택 데이터를 순회하며 저장
        from category.models import Category 
        
        for benefit in benefits_data:
            category_input = benefit.pop('category')
            # category 앱의 Category 모델에서 객체 가져오기
            category_obj, _ = Category.objects.get_or_create(category_name=category_input)
            
            # 실제 CardBenefit 테이블에 연결하여 저장
            CardBenefit.objects.create(card=card, category=category_obj, **benefit)
            
        return card