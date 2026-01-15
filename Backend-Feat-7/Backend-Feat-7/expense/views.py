from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Sum, Avg
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Expense, Subscription
from cards.models import CardBenefit, Card
from users.models import UserCard
from category.models import Category

# 1. 공통 Base 클래스 (인증 및 에러 응답 통일)
class BaseAuthView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    auth_error_message = "조회 실패"
    auth_error_reason = "로그인이 필요하거나 만료되었습니다."
    auth_error_code = "AUTH_REQUIRED"

    def handle_exception(self, exc):
        response = super().handle_exception(exc)
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            return Response({
                "message": self.auth_error_message,
                "error_code": self.auth_error_code,
                "reason": self.auth_error_reason
            }, status=status.HTTP_401_UNAUTHORIZED)
        return response

# 2. 소비 패턴 분석 뷰
class ConsumptionPatternAnalysisView(BaseAuthView):
    @extend_schema(
        summary="소비 패턴 분석",
        description="특정 월의 지출을 그룹 평균과 비교하고 혜택 달성률을 분석합니다.",
        parameters=[
            OpenApiParameter(name='month', description='조회 대상 월 (YYYY-MM)', required=True, type=str)
        ],
        tags=['Expense']
    )
    def get(self, request):
        user = request.user
        target_month = request.query_params.get('month')

        if not target_month:
            return Response({"message": "필수 파라미터(month)가 누락되었습니다."}, status=400)

        try:
            year, month = map(int, target_month.split('-'))
            my_expenses = Expense.objects.filter(
                user=user, 
                spent_at__year=year, 
                spent_at__month=month,
                deleted_at__isnull=True
            )
            
            if not my_expenses.exists():
                return Response({"message": "해당 월의 지출 데이터가 부족합니다."}, status=404)

            my_total_spent = my_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
            group_avg_spent = Expense.objects.filter(
                spent_at__year=year, spent_at__month=month, deleted_at__isnull=True
            ).values('user').annotate(user_total=Sum('amount')).aggregate(Avg('user_total'))['user_total__avg'] or 1
            
            diff_percent = round(((my_total_spent - group_avg_spent) / group_avg_spent) * 100, 1)

            # 실시간 혜택 달성률 계산 로직
            total_benefit_calculated = 0
            user_benefits = CardBenefit.objects.filter(card__usercard__user=user)
            
            for benefit in user_benefits:
                cat_expense = my_expenses.filter(category=benefit.category).aggregate(Sum('amount'))['amount__sum'] or 0
                if cat_expense > 0:
                    raw_benefit = cat_expense * (float(benefit.benefit_rate) / 100)
                    total_benefit_calculated += min(raw_benefit, benefit.benefit_limit or raw_benefit)

            max_limit = user_benefits.aggregate(Sum('benefit_limit'))['benefit_limit__sum'] or 1
            achievement_rate = round((total_benefit_calculated / max_limit) * 100, 1)

            return Response({
                "message": "소비 패턴 분석 데이터 조회 성공",
                "result": {
                    "comparison": {
                        "my_total_spent": my_total_spent,
                        "group_avg_spent": round(group_avg_spent),
                        "diff_percent": diff_percent
                    },
                    "benefit_status": {
                        "total_benefit_received": round(total_benefit_calculated),
                        "max_benefit_limit": max_limit,
                        "achievement_rate": achievement_rate
                    }
                }
            }, status=200)
        except Exception as e:
            return Response({"message": str(e)}, status=500)

# 3. 구독 정보 삭제 (소프트 삭제)
class DeleteSubscription(BaseAuthView):
    @extend_schema(
        summary="구독 정보 삭제",
        description="특정 구독 정보를 소프트 삭제 처리합니다.",
        tags=['Expense']
    )
    def delete(self, request, subs_id):
        try:
            subscription = Subscription.objects.get(
                subs_id=subs_id, 
                user_card__user=request.user,
                deleted_at__isnull=True
            )
            subscription.deleted_at = timezone.now()
            subscription.status = "CANCELED"
            subscription.save()

            return Response({"message": "삭제 성공"}, status=200)
        except Subscription.DoesNotExist:
            return Response({"message": "삭제할 구독 정보를 찾을 수 없습니다."}, status=404)

# 4. 소비 내역 조회
class ShowExpense(BaseAuthView):
    @extend_schema(
        summary="월간 소비 내역 조회",
        description="특정 월의 전체 소비 내역 리스트를 조회합니다.",
        parameters=[
            OpenApiParameter(name='month', description='조회 대상 월 (YYYY-MM)', required=True, type=str)
        ],
        tags=['Expense']
    )
    def get(self, request):
        target_month = request.query_params.get('month')
        if not target_month:
            return Response({"message": "조회 월(month)이 필요합니다."}, status=400)

        try:
            year, month = map(int, target_month.split('-'))
            expenses = Expense.objects.filter(
                user=request.user, spent_at__year=year, spent_at__month=month, deleted_at__isnull=True
            ).select_related('category', 'user_card__card')

            total_spent = expenses.aggregate(total=Sum('amount'))['total'] or 0
            expense_list = [{
                "expense_id": e.expense_id,
                "merchant_name": e.merchant_name,
                "amount": e.amount,
                "spent_at": e.spent_at.strftime("%Y-%m-%dT%H:%M:%S"),
                "category_name": e.category.category_name if e.category else "미분류",
                "card_name": e.user_card.card.card_name if e.user_card else "기타"
            } for e in expenses]

            return Response({
                "message": "월간 지출 내역 조회 성공",
                "result": {"total_spent": total_spent, "expense_list": expense_list}
            }, status=200)
        except Exception as e:
            return Response({"message": str(e)}, status=400)

# 5. 소비 내역 등록
class ExpenseCreateView(BaseAuthView):
    @extend_schema(
        summary="소비 내역 등록",
        description="결제 금액, 가맹점, 카테고리를 입력하여 소비 내역을 등록합니다.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "amount": {"type": "integer", "example": 10000},
                    "merchant_name": {"type": "string", "example": "식당"},
                    "category": {"type": "integer", "example": 1},
                    "spent_at": {"type": "string", "example": "2026-01-14T10:00:00"}
                },
                "required": ["amount", "merchant_name", "category"]
            }
        },
        tags=['Expense']
    )
    def post(self, request):
        try:
            user_cards = UserCard.objects.filter(user=request.user)
            if not user_cards.exists():
                first_card = Card.objects.first()
                if not first_card: return Response({"message": "시스템에 카드 정보가 없습니다."}, status=400)
                user_card_obj = UserCard.objects.create(user=request.user, card=first_card)
            else:
                user_card_obj = user_cards.latest('created_at')

            category_obj = Category.objects.get(category_id=request.data.get('category'))
            Expense.objects.create(
                user=request.user,
                category=category_obj,
                user_card=user_card_obj,
                amount=request.data.get('amount'),
                merchant_name=request.data.get('merchant_name'),
                spent_at=request.data.get('spent_at') or timezone.now()
            )
            return Response({"message": "지출 내역 등록 성공"}, status=201)
        except Exception as e:
            return Response({"message": str(e)}, status=400)

# 6. 구독 내역 조회
class ShowSubscription(BaseAuthView):
    @extend_schema(summary="구독 내역 조회", description="사용자의 활성 구독 목록을 조회합니다.", tags=['Expense'])
    def get(self, request):
        try:
            subscriptions = Subscription.objects.filter(
                user_card__user=request.user, deleted_at__isnull=True
            ).select_related('user_card__card', 'category')
            
            sub_list = [{
                "subs_id": s.subs_id,
                "service_name": s.service_name,
                "monthly_fee": s.monthly_fee,
                "next_billing": s.next_billing.strftime("%Y-%m-%d"),
                "status": s.status,
                "category_name": s.category.category_name if s.category else "기타"
            } for s in subscriptions]

            return Response({"message": "구독 내역 조회 성공", "result": sub_list}, status=200)
        except Exception as e:
            return Response({"message": str(e)}, status=400)