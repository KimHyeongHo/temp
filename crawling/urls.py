from django.urls import path
from .views import StartCrawlingView

urlpatterns = [
    path('start/', StartCrawlingView.as_view(), name='start_crawling'),
]
