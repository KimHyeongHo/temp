from django.urls import path
from .views import ShowCategories  # [설명] 카테고리 목록 조회 뷰 import

app_name = 'category'  # [설명] URL 네임스페이스 설정

urlpatterns = [
    path('categories/', ShowCategories.as_view(), name='show_categories'),  # [설명] 모든 활성 카테고리 목록 조회 엔드포인트 (공통 카테고리)
]