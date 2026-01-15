from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .crawlingProcess import runCrawlingJob
import threading

class StartCrawlingView(APIView):
    """
    카드 데이터 크롤링 및 데이터베이스 저장을 수동으로 실행합니다.

    **요청**
    - `POST /api/v1/crawling/start/`
    
    **설명**
    - 이 엔드포인트를 호출하면 백그라운드에서 크롤링 작업이 시작됩니다.
    - 작업은 시간이 다소 걸릴 수 있으며, 별도의 스레드에서 비동기적으로 처리됩니다.
    - API는 작업이 시작되었음을 즉시 알리는 응답을 반환합니다.
    - 크롤링, 데이터 정제, DB 저장까지의 모든 과정이 포함됩니다.
    
    **응답**
    - `202 ACCEPTED`: 크롤링 작업이 성공적으로 시작되었을 때
    - `500 INTERNAL SERVER ERROR`: 작업 시작에 실패했을 때
    """
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
