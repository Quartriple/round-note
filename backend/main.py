import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg
import redis
import boto3
from botocore.client import Config
from redis import Redis  # <-- [추가]
from rq import Queue     # <-- [추가]
# --- [추가] worker.py 파일에서 'example_task' 함수를 가져옵니다. ---
# (worker.py 파일이 먼저 아래 코드로 수정되어야 합니다)
from worker import example_task 

# -------------------------------------------------------------------
# 1. FastAPI 앱 생성
# -------------------------------------------------------------------
app = FastAPI()

# -------------------------------------------------------------------
# 2. [수정] CORS 설정 (React 앱 주소 추가)
# -------------------------------------------------------------------
origins = [
    os.environ.get("CORS_ORIGIN_LOCAL", "http://localhost:3000"), # 로컬 개발용
    os.environ.get("CORS_ORIGIN_PROD") # Render Static Site URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin for origin in origins if origin], # None이 아닌 origin만 추가
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# 3. 환경 변수에서 '비밀 키' 읽어오기
# -------------------------------------------------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")
REDIS_URL = os.environ.get("REDIS_URL")
NCP_ENDPOINT_URL = os.environ.get("NCP_ENDPOINT_URL")
NCP_ACCESS_KEY = os.environ.get("NCP_ACCESS_KEY")
NCP_SECRET_KEY = os.environ.get("NCP_SECRET_KEY")

# -------------------------------------------------------------------
# 4. "Hello, World!"
# -------------------------------------------------------------------
@app.get("/")
def read_root():
    return {"Hello": "FastAPI is running!"}

# -------------------------------------------------------------------
# 5. Health Check 엔드포인트
# -------------------------------------------------------------------
@app.get("/health-check")
def health_check():
    results = {
        "status": "ok",
        "db": "pending",
        "redis": "pending",
        "storage": "pending"
    }
    
    def get_redis_connection():
        if REDIS_URL and REDIS_URL.startswith("rediss://"):
             return redis.from_url(REDIS_URL, ssl_cert_reqs='required', decode_responses=True)
        elif REDIS_URL:
             return redis.from_url(REDIS_URL, decode_responses=True)
        raise Exception("REDIS_URL이 설정되지 않았습니다.")

    # 1. PostgreSQL
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                if cur.fetchone():
                    results["db"] = "ok"
    except Exception as e:
        results["db"] = f"error: {str(e)[:50]}..."

    # 2. Redis
    try:
        r = get_redis_connection()
        if r.ping():
            results["redis"] = "ok"
    except Exception as e:
        results["redis"] = f"error: {str(e)[:50]}..."

    # 3. NCP Object Storage
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=NCP_ENDPOINT_URL,
            aws_access_key_id=NCP_ACCESS_KEY,
            aws_secret_access_key=NCP_SECRET_KEY,
            config=Config(signature_version='s3v4')
        )
        s3.list_buckets()
        results["storage"] = "ok"
    except Exception as e:
        results["storage"] = f"error: {str(e)[:50]}..."

    if not all(v == "ok" for k, v in results.items() if k != "status"):
        raise HTTPException(status_code=503, detail=results)

    return results

# -------------------------------------------------------------------
# 6. [추가] "Test Job" 엔드포인트
# -------------------------------------------------------------------
def get_redis_for_rq():
    """RQ가 사용할 Redis 연결 객체를 반환합니다."""
    if REDIS_URL and REDIS_URL.startswith("rediss://"):
        return Redis.from_url(REDIS_URL, ssl_cert_reqs='required')
    elif REDIS_URL:
        return Redis.from_url(REDIS_URL)
    raise Exception("REDIS_URL이 설정되지 않아 RQ 큐를 생성할 수 없습니다.")

redis_conn_rq = get_redis_for_rq()

# 'high-priority-queue' 이름으로 큐를 명시적으로 생성합니다.
q = Queue("high-priority-queue", connection=redis_conn_rq)

@app.post("/test-job")
def post_test_job():
    try:
        # 'worker.py'에서 가져온 'example_task'를 큐에 등록
        job = q.enqueue(example_task, "Hello from FastAPI!")
        return {"status": "job enqueued", "job_id": job.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis/RQ error: {str(e)}")