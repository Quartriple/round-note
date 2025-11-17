import os
import asyncio
import wave
import ulid
import logging
from wave import Wave_write
from botocore.client import Config 
import boto3 
from typing import AsyncGenerator

# TODO: (팀원 C) NCP 환경 변수 로드 로직 추가 (필요 시 dotenv.load_dotenv)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s")

class StorageService:
    """오디오 파일의 저장, 로드, 경로 관리를 담당합니다."""

    def __init__(self):
        self.local_storage_path = "./audio_storage" # 로컬 임시 저장소 경로
        # TODO: NCP 클라이언트 초기화
        pass

    # [핵심 변경] 로컬 파일 생성 및 wave.open 관리를 책임집니다.
    def create_local_wave_file(self, meeting_id: str = str(ulid.new())) -> tuple[wave.Wave_write, str]:
        """로컬 오디오 파일을 생성하고 파일 핸들(wave.Wave_write)과 경로를 반환합니다."""
        # TODO: (팀원 C) ulid, os, wave 등 필요 라이브러리 임포트 필요
        os.makedirs(self.local_storage_path, exist_ok=True)
        file_path = os.path.join(self.local_storage_path, f"{meeting_id}.wav")
        
        wave_file = wave.open(file_path, 'wb')
        wave_file.setnchannels(1)
        wave_file.setsampwidth(2)
        wave_file.setframerate(16000)
        logging.info(f"로컬 오디오 저장 시작: {file_path}")
        return wave_file, file_path

    # [핵심 변경] 동기 함수인 writeframes를 to_thread로 감싸는 헬퍼 함수
    async def write_audio_chunk(self, wave_file: wave.Wave_write, audio_data: bytes):
        """오디오 청크를 파일에 비동기로 기록합니다."""
        await asyncio.to_thread(wave_file.writeframes, audio_data)

    # [핵심 변경] wave.close() 역시 비동기로 처리
    async def close_wave_file(self, wave_file: wave.Wave_write):
        """오디오 파일 핸들을 비동기로 닫습니다."""
        await asyncio.to_thread(wave_file.close)
        
    # TODO: (팀원 C) NCP Object Storage 최종 업로드 함수 구현 (추후)
    # async def upload_to_ncp(self, local_path: str, meeting_id: str) -> str: ...