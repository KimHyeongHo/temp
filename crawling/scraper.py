import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

# 수정 내용 형호_13
def scrapeCardGorilla(save_path="card_gorilla_all.html"):
    # 브라우저 옵션 설정
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")

    # 크롬 드라이버 자동 설치 및 실행
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        url = "https://www.card-gorilla.com/search/card"
        print(f"[{url}] 접속 중...")
        driver.get(url)

        # 페이지 로딩 대기
        time.sleep(2)

        clickCount = 0
        
        while True:
            try:
                # "카드 더보기" 버튼 찾기 (클래스명 lst_more)
                # 화면에 보일 때까지 최대 3초 대기
                moreButton = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "lst_more"))
                )

                # 버튼이 화면에 보이지 않거나(display: none) 클릭 불가능 상태면 반복 종료
                if not moreButton.is_displayed():
                    print("더 이상 불러올 카드가 없습니다. (버튼 숨김)")
                    break

                # JavaScript를 사용하여 강제 클릭 (가장 확실한 방법)
                driver.execute_script("arguments[0].click();", moreButton)
                
                clickCount += 1
                
                # 진행 상황 출력 (10번 클릭마다 알림)
                if clickCount % 10 == 0:
                    print(f"현재 {clickCount}회 더보기 클릭 중...")
                
                # 데이터 로딩을 위한 짧은 대기 (네트워크 속도에 따라 조절 가능)
                time.sleep(1.0) 

            except (TimeoutException, NoSuchElementException):
                print("모든 카드가 로딩되었습니다. (더보기 버튼 없음)")
                break
            except StaleElementReferenceException:
                # DOM이 업데이트되어 버튼을 다시 찾아야 하는 경우 재시도
                continue
            except Exception as e:
                print(f"에러 발생: {e}")
                break

        # 최종 로딩된 카드 개수 확인 (옵션)
        cards = driver.find_elements(By.XPATH, '//div[@class="card_list"]//li') 
        print(f"총 {len(cards)}개의 카드가 로딩되었습니다.")

        # 수정 내용 형호_14
        # HTML 파일로 저장
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"저장 완료: {save_path}")

    finally:
        driver.quit()
