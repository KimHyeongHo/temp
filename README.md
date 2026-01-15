# backend.env 파일 만드세요 
## Database Settings (docker-compose.yml과 일치해야 함)
      #SECRET_KEY=본인 키 config/settings.py에 사용됨
      #DB_NAME=본인 데베
      #DB_USER= 본인 유저
      #DB_ROOT_PASSWORD=본인 루트 비번
      #DB_PASSWORD=본인 유저 비번
      #DB_PORT=본인 포트
      #DB_HOST= 본인 호스트 이거 .env 
      #이부분 yml 파일에도 적혀있어요

      #CONNECT_ID=본인 컨넥트 id
      #ACCESS_TOKEN = 로그인시 나오는 토큰 -> 이 두개는 card/test.py에 있는 본인 카드 불러오기에 사용됨

## 이후 yml 맨위의 run all service 클릭 후 도커에서 잘 돌아가는지 컨테이너 확인 
## 오류나면 컨테이너 백앤드라고 적힌부분 누르면 코드 뜨는데 그거 긁어서 ai 돌리면서 수정

### http://localhost:8000/api/v1/docs/ <- 스웨거 실행 주소


# 카테고리 목록 만들기
docker exec -it backend python manage.py shell -c "from category.models import Category; categories = ['식비', '카페/디저트', '대중교통', '편의점', '온라인쇼핑', '대형마트', '주유/차량', '통신/공과금', '디지털구독', '문화/여가', '의료/건강', '교육', '뷰티/잡화', '여행/숙박']; [Category.objects.get_or_create(category_name=name) for name in categories]; print('Category setup complete')"

# load_card 정보 데베에 저장
docker exec -it backend python manage.py load_cards
# update_cards에서 이미지 등 필요한것만 저장
docker exec -it backend python manage.py update_cards
# 카테고리랑 연결해줌
docker exec -it backend python manage.py link_categories
