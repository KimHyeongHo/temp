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
