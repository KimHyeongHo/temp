from django.urls import path
from .views import CardRecommendationView, CardBenefitAnalysisView, CardListView  # [설명] 카드 관련 뷰 import

app_name = 'cards'  # [설명] URL 네임스페이스 설정

urlpatterns = [
    path('recommend/', CardRecommendationView.as_view(), name='card_recommendation'),  # [설명] 카드 추천 조회 엔드포인트
    path('', CardListView.as_view(), name='card_list'),  # [설명] 내 카드 목록 조회 엔드포인트
    path('benefit_analysis/', CardBenefitAnalysisView.as_view(), name='card_benefit_analysis'),  # [설명] 카드 ROI 분석 조회 엔드포인트 (현재는 card_id 미사용)
]