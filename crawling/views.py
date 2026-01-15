from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .crawlingProcess import runCrawlingJob
import threading

class StartCrawlingView(APIView):
    @extend_schema(
        summary="카드 데이터 크롤링 및 데이터베이스 저장",
        description="카드 데이터 크롤링 및 데이터베이스 저장을 수동으로 실행합니다.",
        responses={
            202: OpenApiResponse(description="크롤링 작업이 성공적으로 시작되었습니다."),
            500: OpenApiResponse(description="작업 시작에 실패했습니다.")
        },
        tags=["Crawling"]
    )  

    def post(self, request):
        try:
            # Run the crawling job in a background thread
            crawling_thread = threading.Thread(target=runCrawlingJob)
            crawling_thread.start()
            
            return Response(
                {"message": "Crawling process started in the background."},
                status=status.HTTP_202_ACCEPTED
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to start crawling process: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
