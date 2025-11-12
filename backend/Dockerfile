# 1. 베이스 이미지 선택
FROM python:3.11-slim

# 2. 작업 디렉터리 설정
# 컨테이너 내부의 /app 디렉터리에서 이후 명령을 실행합니다.
WORKDIR /app


# 3. 의존성 설치
# requirements.txt 파일을 컨테이너로 복사합니다.
COPY backend/requirements.txt .

# requirements.txt에 명시된 라이브러리를 설치합니다.
# --no-cache-dir 옵션은 불필요한 캐시를 남기지 않아 이미지 크기를 줄입니다.
RUN pip install --no-cache-dir -r requirements.txt

# 4. 애플리케이션 코드 복사
# 현재 디렉터리(.)의 모든 파일을 컨테이너의 /app 디렉터리로 복사합니다.
COPY backend ./backend

# 5. 애플리케이션 실행
# 컨테이너가 시작될 때 uvicorn을 실행하여 main.py의 app 객체를 
# 0.0.0.0:8000 포트로 서비스합니다. (localhost 대신 0.0.0.0을 사용해야 외부 접근이 가능)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]