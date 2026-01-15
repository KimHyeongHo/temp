import os
import subprocess
from .htmlParser import parseHtmlToCsv
from .pre import cleanCardData
from .scraper import scrapeCardGorilla
import datetime # Import datetime for timestamp

# 파일 이름 정의
htmlFile = "card_gorilla_all.html"
rawCsvFile = "card_gorilla_list.csv"
cleanedCsvFile = "card_gorilla_cleaned.csv"

def runCrawlingJob():
    """
    전체 크롤링 및 데이터 처리 작업을 순서대로 실행합니다.
    1. 웹사이트에서 HTML 스크래핑 (`scraper.py`)
    2. HTML을 파싱하여 CSV로 변환 (`parser.py`)
    3. CSV 데이터 정제 (`pre.py`)
    4. 정제된 데이터를 DB에 로드
    """
    print(f"[{datetime.datetime.now()}] {"=" * 50}")
    print(f"[{datetime.datetime.now()}] 크롤링 및 데이터 처리 작업을 시작합니다.")
    
    try:
        # 1. Scrape HTML
        print(f"[{datetime.datetime.now()}] [단계 1/4] 웹 페이지 스크래핑을 시작합니다...")
        scrapeCardGorilla(htmlFile)
        print(f"[{datetime.datetime.now()}] [단계 1/4] 웹 페이지 스크래핑 완료.")

        # 2. Parse HTML to CSV
        print(f"[{datetime.datetime.now()}] [단계 2/4] HTML 파싱을 시작합니다...")
        parseHtmlToCsv(htmlFile, rawCsvFile)
        print(f"[{datetime.datetime.now()}] [단계 2/4] HTML 파싱 완료. 결과: {rawCsvFile}")

        # 3. Clean CSV data
        print(f"[{datetime.datetime.now()}] [단계 3/4] 데이터 정제를 시작합니다...")
        cleanCardData(rawCsvFile, cleanedCsvFile)
        print(f"[{datetime.datetime.now()}] [단계 3/4] 데이터 정제 완료. 최종 결과: {cleanedCsvFile}")

        # 4. Load data into DB
        print(f"[{datetime.datetime.now()}] [단계 4/4] 정제된 데이터를 데이터베이스에 로드합니다...")
        
        # Capture stdout and stderr for debugging
        process = subprocess.run(
            ["python", "manage.py", "load_cards"], 
            check=True, 
            capture_output=True, 
            text=True
        )
        print(f"[{datetime.datetime.now()}] [단계 4/4] 데이터 로드 완료.")
        if process.stdout:
            print(f"[{datetime.datetime.now()}] Subprocess Stdout:\n{process.stdout}")
        if process.stderr:
            print(f"[{datetime.datetime.now()}] Subprocess Stderr:\n{process.stderr}")

        print(f"[{datetime.datetime.now()}] 모든 작업이 성공적으로 완료되었습니다.")
        print(f"[{datetime.datetime.now()}] {"=" * 50}")

    except subprocess.CalledProcessError as e:
        print(f"[{datetime.datetime.now()}] 작업 중 CalledProcessError 오류가 발생했습니다: {e}")
        print(f"[{datetime.datetime.now()}] Command: {e.cmd}")
        print(f"[{datetime.datetime.now()}] Return Code: {e.returncode}")
        print(f"[{datetime.datetime.now()}] Stdout:\n{e.stdout}")
        print(f"[{datetime.datetime.now()}] Stderr:\n{e.stderr}")
    except Exception as e:
        print(f"[{datetime.datetime.now()}] 작업 중 일반 오류가 발생했습니다: {e}")
    finally:
        # 임시 파일 삭제 (선택 사항)
        if os.path.exists(rawCsvFile):
            # os.remove(rawCsvFile) # Keep for debugging as per previous modification.
            print(f"[{datetime.datetime.now()}] 중간 파일 ({rawCsvFile})이 삭제되지 않고 유지됩니다.")
