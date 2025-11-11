import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg
import redis
from botocore.client import Config
from redis import Redis 
import boto3
from dotenv import load_dotenv

# [신규] API 계층에서 게이트웨이를 import 합니다. (폴더 구조에 맞게 수정)
from .api import realtime_gateway # Pass 1
from .api import batch_gateway    # Pass 2

load_dotenv()

# -------------------------------------------------------------------
# 1. FastAPI 앱 생성 및 설정
# -------------------------------------------------------------------
app = FastAPI()

# 2. CORS 설정
origins = [
    os.environ.get("CORS_ORIGIN_LOCAL", "http://localhost:3000"), 
    os.environ.get("CORS_ORIGIN") # CORS_ORIGIN 환경 변수 사용
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin for origin in origins if origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. [핵심] API 라우터 포함 (경로 분리)
app.include_router(realtime_gateway.router, prefix="/api/v1/realtime", tags=["Realtime"])
# app.include_router(batch_gateway.router, prefix="/api/v1/batch", tags=["Batch & Jobs"])

# 4. 환경 변수 (Health Check용)
DATABASE_URL = os.environ.get("DATABASE_URL")
REDIS_URL = os.environ.get("REDIS_URL")
NCP_ENDPOINT_URL = os.environ.get("NCP_ENDPOINT_URL")
NCP_ACCESS_KEY = os.environ.get("NCP_ACCESS_KEY")
NCP_SECRET_KEY = os.environ.get("NCP_SECRET_KEY")

# -------------------------------------------------------------------
# 5. Health Check (모든 서비스 연결 확인)
# -------------------------------------------------------------------
# (이하 기존 health_check 코드는 변경 없이 그대로 유지)
@app.get("/")
def read_root():
    return {"Hello": "FastAPI is running!"}

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