import os
from dotenv import load_dotenv

load_dotenv()

# 환경 변수에서 Deepgram API 키를 로드합니다.
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")

# streaming_way_DG.py에서 정의된 Deepgram 설정 URL을 가져옵니다.
# 쿼리 파라미터는 전사 품질과 기능(화자 분리, 한국어 등)을 결정합니다.
DEEPGRAM_BASE_URL = "wss://api.deepgram.com/v1/listen"
DEEPGRAM_PARAMS = (
    "?punctuate=true"  # 구두점 추가
    "&language=ko"     # 한국어 지정
    "&model=nova-2"    # 최신 고성능 모델
    "&diarize=true"    # 화자 분리 (Pass 1 핵심 기능)
    "&encoding=linear16" # 오디오 인코딩 형식
    "&sample_rate=16000" # 오디오 샘플링 속도 (마이크/파일 표준)
)

def get_realtime_stt_url() -> tuple[str, dict]:
    """
    FastAPI가 Deepgram WebSocket에 연결하는 데 필요한 URL과 헤더를 반환합니다.
    """
    if not DEEPGRAM_API_KEY:
        raise ValueError("DEEPGRAM_API_KEY 환경 변수가 설정되지 않았습니다.")
        
    full_url = DEEPGRAM_BASE_URL + DEEPGRAM_PARAMS
    headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}
    
    return full_url, headers

# (추후 EleveLabs 배치 STT 함수는 여기에 추가됩니다.)
# async def run_batch_stt(file_path: str):
#     pass