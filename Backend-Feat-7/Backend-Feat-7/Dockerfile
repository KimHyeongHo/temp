FROM python:3.13-slim

#작업 디렉토리 설정
WORKDIR /app

# 필수 시스템 패키지 설치 (mysqlclient 빌드용)
# slim 버전에는 컴파일러가 없으므로 아래 과정이 반드시 필요합니다.
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

#의존성 설치
COPY requirements.txt .

#파이썬 패키지 관리도구 PIP 최신 상태로 업그레이드
RUN pip install --upgrade pip

# 라이브러리 설치
RUN pip install --no-cache-dir -r requirements.txt

#소스 코드 복사
COPY . .


