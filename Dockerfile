FROM python:3.13-slim

#작업 디렉토리 설정
WORKDIR /app

# 환경 변수 설정 (Python 버퍼링 비활성화, .pyc 파일 생성 방지)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 작업 디렉토리 설정
WORKDIR /app

# Install Google Chrome Stable (latest) and its dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    apt-transport-https \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 필수 시스템 패키지 설치 (mysqlclient 빌드용)
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
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


