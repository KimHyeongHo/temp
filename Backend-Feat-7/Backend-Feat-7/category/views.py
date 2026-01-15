from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from .models import Category

# 카테고리 목록 조회 뷰
class ShowCategories(APIView):
    # [설명] 인증 없이도 접근 가능한 공개 API (모든 사용자가 공통으로 사용하는 카테고리)
    
    @extend_schema(
        summary="공통 카테고리 목록 조회",
        description="지출 내역 분류나 카드 혜택 매핑에 사용되는 모든 활성 카테고리 리스트를 반환합니다.",
        responses={
            200: inline_serializer(
                name='CategoryListResponse',
                fields={
                    'categories': serializers.ListField(
                        child=serializers.DictField() # 상세 필드 정의 가능
                    )
                }
            )
        },
        tags=["Common"]
    )
    def get(self, request):
        # 모든 사용자가 공통으로 사용하는 카테고리 목록 조회
        categories = Category.objects.filter(deleted_at__isnull=True)
        
        category_list = [{
            'category_id': c.category_id,
            'category_name': c.category_name,
            'created_at': c.created_at,
        } for c in categories]
        
        return Response({'categories': category_list}, status=status.HTTP_200_OK)