import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg
import redis
import boto3
from botocore.client import Config

# -------------------------------------------------------------------
# 1. FastAPI 앱 생성
# -------------------------------------------------------------------
app = FastAPI()

# -------------------------------------------------------------------
# 2. CORS 설정 (Sprint 0 - Step 4를 위해)
# -------------------------------------------------------------------
# Render Web Service의 환경 변수(Environment Variable)에서
# CORS_ORIGIN = "..." (React가 배포될 주소. 예: https://round-note-web.onrender.com)
# 를 읽어옵니다.
origins = [
    os.environ.get("CORS_ORIGIN", "http://localhost:3000") # 개발용 localhost 포함
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# 3. 환경 변수에서 '비밀 키' 읽어오기 (Sprint 0 - Step 2)
# -------------------------------------------------------------------
# 이 값들은 Render의 환경 변수에서 자동으로 주입됩니다.
DATABASE_URL = os.environ.get("DATABASE_URL")
REDIS_URL = os.environ.get("REDIS_URL")
NCP_ENDPOINT_URL = os.environ.get("NCP_ENDPOINT_URL")
NCP_ACCESS_KEY = os.environ.get("NCP_ACCESS_KEY")
NCP_SECRET_KEY = os.environ.get("NCP_SECRET_KEY")

# -------------------------------------------------------------------
# 4. "Hello, World!" (Render가 실행되는지 확인)
# -------------------------------------------------------------------
@app.get("/")
def read_root():
    return {"Hello": "FastAPI is running!"}

# -------------------------------------------------------------------
# 5. Sprint 0 - Step 3: "Health Check" 엔드포인트
#    (모든 인프라 파이프라인이 뚫렸는지 검증)
# -------------------------------------------------------------------
@app.get("/health-check")
def health_check():
    results = {
        "status": "ok",
        "db": "pending",
        "redis": "pending",
        "storage": "pending"
    }

    # 1. PostgreSQL (Supabase 또는 Render) 연결 테스트
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                if cur.fetchone():
                    results["db"] = "ok"
                else:
                    results["db"] = "failed query"
    except Exception as e:
        results["db"] = f"error: {str(e)[:50]}..." # 에러 메시지 축약

    # 2. Redis (Upstash 또는 Render) 연결 테스트
    try:
        # rediss:// URL은 ssl_cert_reqs='required'가 필요할 수 있습니다.
        # Render 내부망(rediss://)은 보통 'required'가 필요합니다.
        if REDIS_URL.startswith("rediss://"):
             r = redis.from_url(REDIS_URL, ssl_cert_reqs='required', decode_responses=True)
        else:
             r = redis.from_url(REDIS_URL, decode_responses=True)

        if r.ping():
            results["redis"] = "ok"
        else:
            results["redis"] = "failed ping"
    except Exception as e:
        results["redis"] = f"error: {str(e)[:50]}..."

    # 3. NCP Object Storage 연결 테스트
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=NCP_ENDPOINT_URL,
            aws_access_key_id=NCP_ACCESS_KEY,
            aws_secret_access_key=NCP_SECRET_KEY,
            config=Config(signature_version='s3v4')
        )
        s3.list_buckets() # 인증 및 연결 테스트
        results["storage"] = "ok"
    except Exception as e:
        results["storage"] = f"error: {str(e)[:50]}..."

    # 모든 검사가 'ok'가 아니면 500 에러 반환
    if not all(v == "ok" for k, v in results.items() if k != "status"):
        raise HTTPException(status_code=503, detail=results)

    return results

# -------------------------------------------------------------------
# 6. Sprint 0 - Step 3: "Test Job" 엔드포인트
#    (FastAPI -> Redis -> RQ Worker 파이프라인 검증)
# -------------------------------------------------------------------
from redis import Redis
from rq import Queue

q = Queue(connection=Redis.from_url(REDIS_URL))

def example_task(message):
    """RQ Worker가 실행할 간단한 작업"""
    print(f"RQ Worker received message: {message}")
    return f"Message processed: {message}"

@app.post("/test-job")
def post_test_job():
    try:
        job = q.enqueue(example_task, "Hello from FastAPI!")
        return {"status": "job enqueued", "job_id": job.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis/RQ error: {str(e)}")

# (참고: /test-job은 Redis 연결이 /health-check에서 확인된 후 구현해도 됩니다.)