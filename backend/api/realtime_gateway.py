from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import websockets
import json
import logging
import os
import wave
import ulid
import boto3
import tempfile
import redis
from rq import Queue
from datetime import datetime
import dotenv

from ..core import stt_service
from ..core import llm_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s")
dotenv.load_dotenv()

NCP_ENDPOINT_URL = os.environ.get("NCP_ENDPOINT_URL")
NCP_ACCESS_KEY = os.environ.get("NCP_ACCESS_KEY")
NCP_SECRET_KEY = os.environ.get("NCP_SECRET_KEY")
NCP_BUCKET_NAME = os.environ.get("NCP_BUCKET_NAME")

s3_client = boto3.client(
    's3',
    endpoint_url=NCP_ENDPOINT_URL,
    aws_access_key_id=NCP_ACCESS_KEY,
    aws_secret_access_key=NCP_SECRET_KEY
)

redis_conn = redis.Redis(host='redis', port=6379)
rq_queue = Queue('roundnote_jobs', connection=redis_conn)

WAV_SAMPLE_RATE = 16000 # 16kHz (Deepgram 호환)
WAV_CHANNELS = 1       # Mono
WAV_SAMPWIDTH = 2      # 16-bit (2 bytes, streaming_way_DG.py의 'int16'과 동일)

router = APIRouter()

class TranscribeSettings:
    """번역, 요약 등 실시간 기능 활성화 상태를 저장하는 공유 객체"""
    def __init__(self, translate: bool = False, summary: bool = False):
        self.translate = translate
        self.summary = summary
        
# 메인 WebSocket 핸들러
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, translate: bool = True, summary: bool = False):
    """
    메인 WebSocket 핸들러, 클라이언트와 Deepgram 간의 중계 역할을 합니다.
    """
    await websocket.accept()
    print("React <-> FastAPI WebSocket 연결 수립됨.")
    
    settings = TranscribeSettings(translate=translate, summary=summary)
    
    os.makedirs(LOCAL_STORAGE_PATH, exist_ok=True)
    meeting_id = str(ulid.new())
    file_path = os.path.join(LOCAL_STORAGE_PATH, f"{meeting_id}.wav")
    
    wave_file = None
    
    try:
        wave_file = wave.open(file_path, 'wb')
        wave_file.setnchannels(WAV_CHANNELS)
        wave_file.setsampwidth(WAV_SAMPWIDTH)
        wave_file.setframerate(WAV_SAMPLE_RATE)
        logging.info(f"로컬 오디오 저장 시작: {file_path}")
    except Exception as e:
        logging.error(f"오디오 파일 생성 오류: {e}")
        await websocket.close(code=1011, reason="Failed to initialize audio storage.")
    
    try:
        # 1. STT 서비스 코어 호출: Deepgram 연결 정보 획득
        dg_url, dg_headers = stt_service.get_realtime_stt_url()
        
        # 2. Deepgram WebSocket에 연결
        async with websockets.connect(dg_url, additional_headers=dg_headers) as dg_websocket:
            print(f"Deepgram 연결 성공. 양방향 중계 시작.")

            # 3. 비동기 태스크 생성: React <-> Deepgram 양방향 중계
            #    asyncio.create_task는 즉시 실행되지만 결과를 기다리지 않습니다.
            forward_task = asyncio.create_task(
                handle_client_uplink(websocket, dg_websocket, settings, wave_file)
            )
            receive_task = asyncio.create_task(
                forward_to_client(websocket, dg_websocket, settings)
            )
            
            # 4. 두 태스크 중 하나가 끝날 때까지 대기
            #    (보통 클라이언트 연결이 끊길 때까지 계속 실행됩니다.)
            done, pending = await asyncio.wait(
                [forward_task, receive_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for task in pending:
                task.cancel()
                # 취소가 완료될 때까지 잠시 대기
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    except WebSocketDisconnect:
        # 5. React가 연결을 끊었을 때
        print("React 클라이언트 연결 종료 (정상)")
    except Exception as e:
        # 6. Deepgram 연결 실패 등 오류 발생 시
        print(f"WebSocket 파이프라인 오류: {e}")
        await websocket.send_json({"type": "error", "message": f"서버 오류: {e}"})
    finally:
        if wave_file:
            try:
                # wave.close() 역시 동기 함수이므로 to_thread 사용
                await asyncio.to_thread(wave_file.close)
                logging.info(f"🔴 WebSocket 핸들러 종료 및 파일 저장 완료: {file_path}")
            except Exception as e:
                logging.error(f"❌ wave_file 닫기 실패: {e}")
        else:
            logging.info(f"🔴 WebSocket 핸들러 종료 (파일 객체 없음)")



async def handle_client_uplink(client_ws: WebSocket, dg_ws: websockets.WebSocketClientProtocol, settings: TranscribeSettings, wave_file: wave.Wave_write):
    """
    React로부터 오디오 청크(bytes)와 제어 메시지(JSON/text)를 모두 받아 처리합니다.
    """
    print("Uplink Handler: 오디오 및 제어 메시지 수신 시작.")
    try:
        while True:
            # 1. [핵심] bytes, text 등 모든 유형의 메시지를 수신 (논블로킹 await)
            message = await client_ws.receive()

            # 2. bytes (오디오 데이터): Deepgram으로 즉시 중계
            if message.get("bytes"):
                audio_data = message["bytes"]
                
                if len(audio_data) > 0:
                    await dg_ws.send(audio_data)
                    
                    try: 
                        await wave_file.writeframes(wave_file.writeframes, audio_data)
                    except Exception as e:
                        logging.error(f"오디오 청크 로컬 쓰기 오류: {e}")
                else:
                    print("UPLINK RECEIVED: 0 bytes. Skipping forward.")

            elif message.get("text"):
                # 3. text (제어 메시지): JSON으로 파싱하여 설정 변경
                try:
                    control_msg = json.loads(message["text"])
                    command = control_msg.get("command")
                    value = control_msg.get("value")
                    
                    if command == "SET_TRANSLATE" and isinstance(value, bool):
                        settings.translate = value # 공유 상태 업데이트
                        print(f"--> [CONTROL] 번역 기능 상태 변경: {value}")
                        # 클라이언트에게 설정이 바뀌었음을 알리는 피드백 (선택적)
                        await client_ws.send_json({"type": "setting_update", "translate": value})
                    # (추후 "SET_SUMMARY" 등 다른 명령어도 여기서 처리)
                        
                except json.JSONDecodeError:
                    print(f"Uplink Handler: 비정상 텍스트 메시지 수신 무시: {message['text']}")
            
    except WebSocketDisconnect:
        print("Uplink Handler: 클라이언트 연결 끊김 감지.")
    except Exception as e:
        print(f"Uplink Handler 오류: {e}")
    finally:
        try:
            await dg_ws.send(json.dumps({"type": "CloseStream"}))
        except Exception:
            pass
        try:
            # 이 시점에 dg_ws가 아직 열려있다면 닫아줍니다.
            await dg_ws.close()
        except Exception:
            pass



async def forward_to_client(client_ws: WebSocket, dg_ws: websockets.WebSocketClientProtocol, settings: TranscribeSettings):
    """
    Deepgram(dg_ws)으로부터 전사 결과를 받아 React(client_ws)로 전달하고,
    공유 상태(settings)에 따라 번역 태스크를 생성합니다.
    """
    print("DG Receiver: 텍스트 수신 및 중계 시작.")
    try:
        # 1. Deepgram으로부터 메시지를 비동기로 반복 수신 (Async For)
        async for message in dg_ws:
            # print("DG RECEIVER: Message received from Deepgram.")
            
            result = json.loads(message)
            
            if result.get("type") == "Metadata" or result.get("type") == "UtteranceEnd":
                print(f"DG RECEIVER: Skipped Deepgram message type: {result.get('type')}")
                continue
            
            # Deepgram 응답에서 전사 텍스트 추출 (로직은 streaming_way_DG.py 재활용)
            transcript = result.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")
            if not transcript:
                continue

            if result.get("is_final"):
                # 2. 최종 텍스트 처리: 화자 정보와 함께 최종 문장 구성
                words = result.get("channel", {}).get("alternatives", [{}])[0].get("words", [])
                speaker_id = words[0].get("speaker") if words else None
                speaker_tag = f"[Speaker {speaker_id}] " if speaker_id is not None else ""
                final_text = speaker_tag + transcript
                
                # 3. (React 전송) 최종 전사 텍스트를 React로 전송
                await client_ws.send_json({"type": "final_transcript", "text": final_text})
                
                if settings.translate:
                    asyncio.create_task(
                        get_translation_and_send(client_ws, final_text)
                    )
                
            else:
                # 5. 임시 텍스트 처리: React로 임시 전사 텍스트 전송
                await client_ws.send_json({"type": "partial_transcript", "text": transcript})
                
    except WebSocketDisconnect:
        # 이 함수가 종료되면 websocket_endpoint의 gather도 종료됩니다.
        print("DG Receiver: 클라이언트 연결 끊김 감지.")
    except Exception as e:
        print(f"DG Receiver 오류: {e}")



async def get_translation_and_send(client_ws: WebSocket, text: str):
    """
    Core Service를 호출하여 번역하고 결과를 React로 전송합니다.
    이 함수는 'forward_to_client'에서 asyncio.create_task로 호출됩니다.
    """
    print(f"Translation Task Started for: {text}")
    try:
        # 1. core/llm_service.py의 코어 함수 호출 (실제 API 통신)
        translated_text = await llm_service.get_translation(text)
        
        # 2. 번역 결과를 React로 전송 (논블로킹)
        await client_ws.send_json({
            "type": "translation",
            "original_text": text,
            "translated_text": translated_text
        })
        print(f"Translation Task Finished for: {text}")
        
    except Exception as e:
        print(f"OpenAI 번역 오류: {e}")
        # 오류 발생 시 클라이언트에게 알림
        await client_ws.send_json({"type": "error", "message": f"Translation failed: {e}"})