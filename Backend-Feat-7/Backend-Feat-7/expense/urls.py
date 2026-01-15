from django.urls import path
from .views import (
    ConsumptionPatternAnalysisView,  # [설명] 소비 패턴 분석 뷰
    DeleteSubscription,  # [설명] 구독 삭제 뷰
    ShowSubscription,  # [설명] 구독 목록 조회 뷰
    ShowExpense,  # [설명] 월간 지출 내역 조회 뷰
    ExpenseCreateView,  # [설명] 테스트용 지출 등록 뷰
)

urlpatterns = [
    path('register/', ExpenseCreateView.as_view(), name='expense-register'),  # [설명] 테스트용 지출 등록

    # 소비 패턴 분석 (예: /api/analysis/?month=2026-01)
    path('analysis/', ConsumptionPatternAnalysisView.as_view(), name='consumption-analysis'),  # [설명] 소비 패턴 분석
    
    # 지출 내역 조회 (예: /api/expenses/?month=2026-01)
    path('expenses/', ShowExpense.as_view(), name='show-expense'),  # [설명] 월간 지출 내역 조회
    
    # 구독 목록 조회 및 삭제
    path('subscriptions/', ShowSubscription.as_view(), name='show-subscription'),  # [설명] 구독 목록 조회
    path('subscriptions/<int:subs_id>/', DeleteSubscription.as_view(), name='delete-subscription'),  # [설명] 구독 단건 삭제
]