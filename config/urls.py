"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    #path('admin/', admin.site.urls),
    
    # [변경] 모든 API 경로에 v1 버전 적용
    path('api/v1/users/', include('users.urls')),      # 예: /api/v1/users/login/
    path('api/v1/expense/', include('expense.urls')),  # 예: /api/v1/expense/analysis/
    path('api/v1/chat/', include('chat.urls')),        # 예: /api/v1/chat/make_room/
    path('api/v1/cards/', include('cards.urls')),      # 예: /api/v1/cards/recommend/
    path('api/v1/category/', include('category.urls')),# 예: /api/v1/category/categories/
    path('api/v1/crawling/', include('crawling.urls')),

    # drf-spectacular 스웨거 및 레독 문서화 경로
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
