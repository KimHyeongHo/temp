from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from datetime import timedelta
from .models import CardBenefit  # [설명] 본인 앱(cards)의 모델
from users.models import UserCard  # [설명] users 앱의 User 모델
from expense.models import Expense  # [설명] expense 앱의 Expense 모델
from django.db.models import Avg, Sum  # [설명] 집계 함수 import
from .serializers import CardSerializer, RecommendedCardSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter  # [추가] drf-spectacular 스웨거 설정을 위해 import
from category.models import Category
# 사용자가 보유한 모든 카드 조회, 카드 등록, 카드 추천, 카드 혜택 효율 분석 API 구현

# 공통 에러 응답 함수 (중복 제거)
def error_response(message, code, status_code, reason=None):
    # [설명] 모든 뷰에서 공통으로 사용하는 에러 응답 포맷 함수
    res = {"message": message, "code": code}
    if reason:
        res["reason"] = reason
    return Response(res, status=status_code)

# 카드 목록 조회 뷰
class CardListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="내 카드 목록 조회",
        description="현재 로그인한 사용자가 등록한 모든 카드 리스트를 가져옵니다.",
        responses={200: CardSerializer(many=True)},
        tags=["Cards"]
    )
    def get(self, request):
        # UserCard 목록을 가져옵니다.
        user_card_queryset = UserCard.objects.filter(user=request.user).select_related('card')
        
        # [중요] 시리얼라이저는 'Card' 모델을 대상으로 하므로, UserCard 객체에서 card 객체들만 뽑아야함
        cards = [uc.card for uc in user_card_queryset]
        
        # 뽑아낸 card 리스트를 시리얼라이저에 넣습니다.
        serializer = CardSerializer(cards, many=True)
        return Response({
            "message": "내 카드 목록 조회 성공",
            "cards": serializer.data
        }, status=status.HTTP_200_OK)

# 카드 추천 뷰
class CardRecommendationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        three_months_ago = timezone.now() - timedelta(days=90)

        # 1. 최근 3개월간 가장 많이 소비한 카테고리 Top 1 추출
        top_category_data = Expense.objects.filter(
            user=user,
            spent_at__gte=three_months_ago,
            deleted_at__isnull=True
        ).values('category').annotate(
            total_amount=Sum('amount')
        ).order_by('-total_amount').first()

        if not top_category_data:
            return error_response("추천 실패", "NO_DATA", 404, "최근 지출 내역이 없습니다.")

        top_category_id = top_category_data['category']

        # 2. 해당 카테고리 혜택이 높은 순으로 카드 조회 (중복 제거 필수)
        recommended_benefits = CardBenefit.objects.filter(
            category_id=top_category_id,
            deleted_at__isnull=True
        ).select_related('card').order_by('-benefit_rate')

        # [수정] 동일한 카드가 여러 번 나오지 않도록 중복 제거하며 5개 추출
        seen_cards = set()
        unique_cards = []
        for benefit in recommended_benefits:
            if benefit.card.card_id not in seen_cards:
                unique_cards.append(benefit.card)
                seen_cards.add(benefit.card.card_id)
            if len(unique_cards) >= 5: break

        serializer = RecommendedCardSerializer(unique_cards, many=True)
        return Response({
            "message": "카드 추천 목록 조회 성공",
            "target_category_id": top_category_id,
            "recommended_cards": serializer.data # 데이터가 잘 담겨 나가는지 확인
        }, status=200)
    
# 카드 혜택 효율 분석 뷰
class CardBenefitAnalysisView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="종합 카드 분석 및 추천",
        description="보유 카드의 효율 분석 결과와 소비 패턴 기반 추천 카드 TOP 5를 함께 반환합니다.",
        tags=["Analysis"]
    )
    def get(self, request):
        user = request.user
        three_months_ago = timezone.now() - timedelta(days=90)
        
        try:
            # --- 1. 내 카드 효율(ROI) 분석 로직 ---
            user_cards = UserCard.objects.filter(user=user).select_related('card')
            my_cards_analysis = []
            seen_card_ids = set() # 내 카드 ID 저장용

            for uc in user_cards:
                card = uc.card
                seen_card_ids.add(card.card_id) # 추천 리스트에서 제외하기 위해 추가
                
                total_benefit = 0
                benefits = CardBenefit.objects.filter(card=card)
                
                for benefit in benefits:
                    expense_sum = Expense.objects.filter(
                        user=user, category=benefit.category,
                        spent_at__gte=three_months_ago, deleted_at__isnull=True
                    ).aggregate(Sum('amount'))['amount__sum'] or 0
                    
                    if expense_sum > 0:
                        calc = expense_sum * (float(benefit.benefit_rate) / 100)
                        total_benefit += min(calc, benefit.benefit_limit) if benefit.benefit_limit else calc

                annual_fee = max(card.annual_fee_domestic, 1000)
                monthly_avg = total_benefit / 3
                roi = ((monthly_avg * 12) / annual_fee) * 100

                my_cards_analysis.append({
                    "card_id": card.card_id,
                    "card_name": card.card_name,
                    "roi_ratio": round(roi, 1),
                    "monthly_benefit_avg": round(monthly_avg),
                    "comment": "효율이 좋습니다!" if roi > 100 else "무난한 혜택입니다."
                })
            
            my_cards_analysis.sort(key=lambda x: x['roi_ratio'], reverse=True)

            # --- 2. 맞춤 카드 추천 로직 ---
            top_category_data = Expense.objects.filter(
                user=user, spent_at__gte=three_months_ago, deleted_at__isnull=True
            ).values('category').annotate(
                total_amount=Sum('amount')
            ).order_by('-total_amount').first()

            recommended_cards_data = []
            target_category_name = "데이터 부족"
            
            # [추가] 시리즈 카드(이름 유사 카드) 중복을 막기 위한 집합
            seen_card_names = set() 

            if top_category_data:
                target_category_id = top_category_data['category']
                target_category_name = Category.objects.get(category_id=target_category_id).category_name
                
                recommended_benefits = CardBenefit.objects.filter(
                    category_id=target_category_id, deleted_at__isnull=True
                ).select_related('card').order_by('-benefit_rate')

                for b in recommended_benefits:
                    card = b.card
                    
                    # A. 이미 내가 가진 카드는 추천에서 제외
                    if card.card_id in seen_card_ids:
                        continue
                    
                    # B. 이름 중복 체크 로직 (추가된 부분)
                    # 카드 이름에서 공백을 제거하고 앞 7글자만 따서 비교합니다.
                    # '신한카드 구독 좋아요'와 'SPOTV NOW 신한카드 구독 좋아요'를 같은 군으로 묶음
                    card_prefix = card.card_name.replace(" ", "")[:7]
                    
                    if card_prefix not in seen_card_names:
                        recommended_cards_data.append({
                            "card_id": card.card_id,
                            "card_name": card.card_name,
                            "benefit_rate": b.benefit_rate,
                            "main_category": target_category_name
                        })
                        seen_card_names.add(card_prefix) # 사용된 이름으로 등록
                    
                    if len(recommended_cards_data) >= 5: 
                        break

            # --- 3. 최종 응답 ---
            return Response({
                "message": "종합 분석 및 추천 성공",
                "result": {
                    "my_cards": my_cards_analysis,
                    "recommendations": {
                        "target_category": target_category_name,
                        "cards": recommended_cards_data
                    }
                }
            }, status=200)

        except Exception as e:
            return Response({"message": f"분석 중 에러 발생: {str(e)}"}, status=500)