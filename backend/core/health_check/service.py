import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg
import redis
from botocore.client import Config
from redis import Redis 
import boto3
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
REDIS_URL = os.environ.get("REDIS_URL")
NCP_ENDPOINT_URL = os.environ.get("NCP_ENDPOINT_URL")
NCP_ACCESS_KEY = os.environ.get("NCP_ACCESS_KEY")
NCP_SECRET_KEY = os.environ.get("NCP_SECRET_KEY")

def get_redis_connection():
    """Redis 연결 객체를 반환합니다."""
    if REDIS_URL and REDIS_URL.startswith("rediss://"):
         return redis.from_url(REDIS_URL, ssl_cert_reqs='required', decode_responses=True)
    elif REDIS_URL:
         return redis.from_url(REDIS_URL, decode_responses=True)
    raise Exception("REDIS_URL이 설정되지 않았습니다.")

# TODO: (팀원 C) HealthCheckStatus Pydantic 모델 정의 (반환 타입을 명확히 하기 위해)

def run_full_health_check() -> Dict[str, Any]:
    """모든 주요 서비스(DB, Redis, Storage)의 연결 상태를 확인합니다."""
    results = {
        "status": "ok",
        "db": "pending",
        "redis": "pending",
        "storage": "pending"
    }

    # 1. PostgreSQL Check
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                if cur.fetchone():
                    results["db"] = "ok"
    except Exception as e:
        results["db"] = f"error: {str(e)[:50]}..."

    # 2. Redis Check
    try:
        r = get_redis_connection()
        if r.ping():
            results["redis"] = "ok"
    except Exception as e:
        results["redis"] = f"error: {str(e)[:50]}..."

    # 3. NCP Object Storage Check
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
        results["status"] = "error" # Health Check 실패 시 상태 업데이트
        raise HTTPException(status_code=503, detail=results)

    return results

# TODO: (팀원 C) Health Check 로직에 Deepgram, OpenAI 등 외부 LLM/STT 연결 확인 추가 (선택 사항)