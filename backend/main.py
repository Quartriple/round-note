import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import psycopg
import redis
from botocore.client import Config
from redis import Redis 
import boto3
from dotenv import load_dotenv

from .api.v1.health_check.endpoints import router as health_router
from .api.v1.auth.endpoints import router as auth_router
from .api.v1.meetings.endpoints import router as meetings_router
from .api.v1.realtime.endpoints import router as realtime_router


load_dotenv()

# 1. FastAPI 앱 생성 및 설정
app = FastAPI()

# 세션 미들웨어 추가 (Google OAuth에 필요)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "your-secret-key-here"))

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

# 3. API 라우터 포함
app.include_router(health_router, prefix="/api/v1/health-check", tags=["Health"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(meetings_router, prefix="/api/v1/meetings", tags=["Meetings"])
app.include_router(realtime_router, prefix="/api/v1/realtime", tags=["Realtime"])
# TODO: (팀원 A) 추후 보고서(Report) 조회 API 필요 시 라우터 추가


@app.get("/")
def read_root():
    return {"Hello": "FastAPI is running!"}