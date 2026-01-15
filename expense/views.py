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
        description="특정 월의 지출을 그룹 평균과 비교하고 혜택 달성률 및 백분위를 분석합니다.",
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
            
            # 1. 내 지출 데이터 조회
            my_expenses = Expense.objects.filter(
                user=user, 
                spent_at__year=year, 
                spent_at__month=month,
                deleted_at__isnull=True
            )
            
            my_total_spent = my_expenses.aggregate(Sum('amount'))['amount__sum'] or 0

            # 2. 그룹(전체 유저) 평균 및 백분위 계산
            # 모든 유저의 해당 월 총 지출 리스트를 가져옴
            all_user_totals = Expense.objects.filter(
                spent_at__year=year, 
                spent_at__month=month, 
                deleted_at__isnull=True
            ).values('user').annotate(user_total=Sum('amount')).order_by('user_total')

            total_users = all_user_totals.count()
            group_avg_spent = all_user_totals.aggregate(Avg('user_total'))['user_total__avg'] or 1
            
            # 내 위치(백분위) 계산
            my_rank = 0
            for index, entry in enumerate(all_user_totals):
                if entry['user_total'] >= my_total_spent:
                    my_rank = index
                    break
            
            # 백분위 (0~100, 낮을수록 적게 씀)
            percentile = round((my_rank / total_users) * 100) if total_users > 0 else 0
            diff_percent = round(((my_total_spent - group_avg_spent) / group_avg_spent) * 100, 1)

            # 3. 실시간 혜택 달성률 계산 (게이지바용)
            total_benefit_received = 0
            user_benefits = CardBenefit.objects.filter(card__usercard__user=user)
            
            for benefit in user_benefits:
                cat_expense = my_expenses.filter(category=benefit.category).aggregate(Sum('amount'))['amount__sum'] or 0
                if cat_expense > 0:
                    raw_benefit = cat_expense * (float(benefit.benefit_rate) / 100)
                    total_benefit_received += min(raw_benefit, benefit.benefit_limit or raw_benefit)

            max_limit = user_benefits.aggregate(Sum('benefit_limit'))['benefit_limit__sum'] or 1
            achievement_rate = round((total_benefit_received / max_limit) * 100, 1)

            # 4. JSON 응답 (사용자 요구 형식 반영)
            return Response({
                "message": "소비 패턴 분석 데이터 조회 성공",
                "result": {
                    "user_id": user.user_id,
                    "comparison": {
                        "my_total_spent": my_total_spent,
                        "group_avg_spent": round(group_avg_spent),
                        "diff_percent": diff_percent,
                        "percentile": percentile
                    },
                    "benefit_status": {
                        "total_benefit_received": round(total_benefit_received),
                        "max_benefit_limit": max_limit,
                        "achievement_rate": min(achievement_rate, 100.0) # 100% 초과 방지
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


# 5. 구독 내역 조회 (보안 및 데이터 보완 버전)
class ShowSubscription(BaseAuthView):
    @extend_schema(summary="구독 내역 조회", description="사용자의 활성 구독 목록을 조회합니다.", tags=['Expense'])
    def get(self, request):
        try:
            # 결제일이 가까운 순서로 정렬 추가
            subscriptions = Subscription.objects.filter(
                user=request.user,  # user_card를 통하는 것보다 직접 연결된 user 필드 사용 권장
                deleted_at__isnull=True
            ).select_related('user_card__card', 'category').order_by('next_billing')
            
            sub_list = []
            for s in subscriptions:
                # 오늘 기준으로 결제일까지 남은 일수 계산 (선택 사항)
                days_left = (s.next_billing - timezone.now().date()).days

                sub_list.append({
                    "subs_id": s.subs_id,
                    "service_name": s.service_name,
                    "monthly_fee": s.monthly_fee,
                    "next_billing": s.next_billing.strftime("%Y-%m-%d"),
                    "d_day": days_left, # "결제일까지 D-3" 등으로 활용 가능
                    "status": s.status, # "ACTIVE"
                    "status_kor": s.get_status_display(), # "구독중" (모델의 choices 기반 자동 변환)
                    "category_name": s.category.category_name if s.category else "기타"
                })

            return Response({
                "message": "구독 내역 조회 성공", 
                "result": sub_list
            }, status=200)
        except Exception as e:
            return Response({"message": str(e)}, status=400)