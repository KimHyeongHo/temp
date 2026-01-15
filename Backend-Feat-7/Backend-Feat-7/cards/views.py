from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from datetime import timedelta
from .models import Card, CardBenefit  # [설명] 본인 앱(cards)의 모델
from users.models import User  # [설명] users 앱의 User 모델
from expense.models import Expense  # [설명] expense 앱의 Expense 모델
from django.db.models import Avg, Sum  # [설명] 집계 함수 import
from .serializers import CardRegisterSerializer, CardSerializer, RecommendedCardSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter  # [추가] drf-spectacular 스웨거 설정을 위해 import

# 사용자가 보유한 모든 카드 조회, 카드 등록, 카드 추천, 카드 혜택 효율 분석 API 구현

# 공통 에러 응답 함수 (중복 제거)
def error_response(message, code, status_code, reason=None):
    # [설명] 모든 뷰에서 공통으로 사용하는 에러 응답 포맷 함수
    res = {"message": message, "code": code}
    if reason:
        res["reason"] = reason
    return Response(res, status=status_code)


# 카드 등록 뷰
class CardRegisterView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="카드 및 혜택 등록",
        description="사용자가 새로운 카드 정보와 해당 카드의 카테고리별 혜택 정보를 등록합니다.",
        request=CardRegisterSerializer,
        responses={201: CardRegisterSerializer, 400: None},
        tags=["Cards"]
    )
    def post(self, request):
        serializer = CardRegisterSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": 201,
                "message": "카드 및 혜택 등록 성공",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return error_response("카드 등록 실패", "INVALID_DATA", status.HTTP_400_BAD_REQUEST, serializer.errors)

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
        cards = Card.objects.filter(user=request.user)
        serializer = CardSerializer(cards, many=True)
        return Response({
            "message": "내 카드 목록 조회 성공",
            "cards": serializer.data
        }, status=status.HTTP_200_OK)

# 카드 추천 뷰
class CardRecommendationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="소비 패턴 기반 카드 추천",
        description="최근 3개월간 가장 많이 소비한 카테고리를 분석하여 혜택율이 높은 카드 TOP 5를 추천합니다.",
        responses={200: RecommendedCardSerializer(many=True), 404: None},
        tags=["Analysis"]
    )
    def get(self, request):
        user = request.user
        three_months_ago = timezone.now() - timedelta(days=90)

        # 1. 최근 3개월간 유저가 가장 많이 소비한 카테고리 Top 1 추출
        top_category_data = Expense.objects.filter(
            user=user,
            spent_at__gte=three_months_ago,
            deleted_at__isnull=True
        ).values('category').annotate(
            total_amount=Sum('amount')
        ).order_by('-total_amount').first()

        if not top_category_data:
            return error_response("카드 추천 목록 조회 실패", "NO_EXPENSE_DATA", 
                                 status.HTTP_404_NOT_FOUND, "최근 지출 내역이 부족하여 맞춤 추천이 어렵습니다.")

        top_category_id = top_category_data['category']

        try:
            recommended_benefits = CardBenefit.objects.filter(
                category_id=top_category_id,
                deleted_at__isnull=True
            ).select_related('card').order_by('-benefit_rate')[:5]

            cards = [benefit.card for benefit in recommended_benefits]
            serializer = RecommendedCardSerializer(cards, many=True)
            
            return Response({
                "message": "카드 추천 목록 조회 성공",
                "target_category_id": top_category_id,
                "recommended_cards": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return error_response("카드 추천 목록 조회 실패", "RECOMMENDATION_ERROR", 
                                 status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))

# 카드 혜택 효율 분석 뷰
class CardBenefitAnalysisView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="카드 ROI(혜택 효율) 분석",
        description="사용자의 지출 내역을 바탕으로 현재 보유한 카드가 연회비 대비 얼마나 혜택을 주는지 분석합니다.",
        parameters=[
            OpenApiParameter(name='card_id', description='분석할 카드의 ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={200: None}, # 상세 응답 스키마는 필요시 추가 정의 가능
        tags=["Analysis"]
    )
    def get(self, request, card_id):
        user = request.user
        three_months_ago = timezone.now() - timedelta(days=90)
        
        if not Expense.objects.filter(user=user).exists():
            return error_response("카드 ROI 분석 실패", "NO_EXPENSE_DATA", 
                                 status.HTTP_404_NOT_FOUND, "분석할 지출 내역이 존재하지 않습니다.")

        try:
            user_cards = Card.objects.filter(user=user)
            cards_data = []
            
            for card in user_cards:
                total_benefit_received = 0
                actual_annual_fee = card.annual_fee_domestic if card.annual_fee_domestic > 0 else 1
                
                benefits = CardBenefit.objects.filter(card=card)
                
                for benefit in benefits:
                    category_expense = Expense.objects.filter(
                        user=user,
                        category=benefit.category,
                        spent_at__gte=three_months_ago
                    ).aggregate(total=Sum('amount'))['total'] or 0
                    
                    if category_expense > 0:
                        calculated_benefit = category_expense * (float(benefit.benefit_rate) / 100)
                        real_benefit = min(calculated_benefit, benefit.benefit_limit) if benefit.benefit_limit else calculated_benefit
                        total_benefit_received += real_benefit

                monthly_avg = total_benefit_received / 3
                yearly_est = monthly_avg * 12
                roi = (yearly_est / actual_annual_fee) * 100
                
                cards_data.append({
                    "card_id": card.card_id,
                    "card_name": card.card_name,
                    "annual_fee": card.annual_fee_domestic,
                    "monthly_benefit_avg": round(monthly_avg, 0),
                    "yearly_benefit_est": round(yearly_est, 0),
                    "roi_ratio": round(roi, 1),
                    "comment": "혜택이 좋습니다!" if roi > 100 else "연회비 대비 효율이 낮습니다."
                })

            return Response({
                "message": "카드 ROI 분석 성공",
                "result": {"cards": cards_data}
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return error_response("카드 ROI 분석 실패", "CALCULATION_ERROR", 
                                 status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))