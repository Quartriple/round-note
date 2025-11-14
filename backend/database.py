import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import dotenv

dotenv.load_dotenv()

# 1. .env에서 DB URL 로드
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL 환경 변수가 .env 파일에 설정되지 않았습니다.")

# 2. SQLAlchemy 엔진 생성
engine = create_engine(DATABASE_URL)

# 3. DB 세션 생성자 (SessionLocal) 정의
#    이것이 FastAPI와 Worker에서 사용할 DB 세션입니다.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# (참고: Base는 models.py에서 임포트하여 사용)
# from .models import Base