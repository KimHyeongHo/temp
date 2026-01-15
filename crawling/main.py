import time
import schedule
from .crawlingProcess import runCrawlingJob
import datetime # Import datetime for timestamp

if __name__ == "__main__":
    print(f"[{datetime.datetime.now()}] 크롤링 스케줄러가 시작되었습니다.")
    print(f"[{datetime.datetime.now()}] 매주 월요일 03:00에 작업이 실행됩니다.")

    # 스케줄 등록: 매주 월요일 새벽 3시에 실행
    schedule.every().monday.at("03:00").do(runCrawlingJob)

    # # 테스트용: 1분마다 실행
    # schedule.every(1).minutes.do(runCrawlingJob)
    
    # 프로그램 시작 시 즉시 1회 실행
    print(f"[{datetime.datetime.now()}] 즉시 1회 실행합니다.")
    try:
        runCrawlingJob()
        print(f"[{datetime.datetime.now()}] 즉시 1회 실행 완료.")
    except Exception as e:
        print(f"[{datetime.datetime.now()}] 즉시 1회 실행 중 오류 발생: {e}")

    while True:
        schedule.run_pending()
        time.sleep(1)
