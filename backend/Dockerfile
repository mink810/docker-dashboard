# Python 3.11 경량 이미지 기반 (slim = 최소 패키지로 이미지 크기 축소)
FROM python:3.11-slim

# 컨테이너 내 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 후 설치 (캐시 활용: requirements 변경 시에만 이 단계부터 재빌드)
COPY requirements.txt .
RUN pip install -r requirements.txt

# 애플리케이션 소스 코드 복사
COPY . .

# FastAPI 앱을 Uvicorn으로 실행 (0.0.0.0 = 외부 접근 허용, 포트 8000)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
