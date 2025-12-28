# 1. 베이스 이미지 설정
FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /app

# 2. 시스템 라이브러리 업데이트 및 빌드 도구 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 3. requirements.txt 파일을 먼저 복사
# (소스 코드 전체를 복사하기 전에 미리 복사해야 캐시 효율이 좋습니다)
COPY requirements.txt .

# 4. pip 최신화 및 패키지 일괄 설치
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. 나머지 소스 코드 복사
COPY . .