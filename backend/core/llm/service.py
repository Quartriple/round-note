import os
import asyncio
from openai import AsyncOpenAI
from typing import List
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    """LLM 서비스: 번역, 요약, 액션 아이템 추출 등 모든 LLM 관련 로직을 담당합니다."""

    def __init__(self):
        
        OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        # TODO: (팀원 B) LangChain, RAG 관련 객체 초기화 (추후)

    def generate_summary(self, texts: List[str]) -> str:
        # Placeholder: join the texts
        return " ".join(texts)


    async def get_translation(self, text: str) -> str:
        """
        실시간으로 텍스트를 번역하는 코어 함수.
        (streaming_way_DG.py의 translation_thread 로직 재활용)
        """
        if not text.strip():
            return ""
            
        try:
            # streaming_way_DG.py에서 사용한 모델과 프롬프트 재현
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a highly skilled real-time translator. Translate the following Korean text to English. Respond with only the translated text.",
                    },
                    {"role": "user", "content": text},
                ],
                model="gpt-4.1-mini", 
            )
            return chat_completion.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"LLM Translation Error: {e}")
            return f"[Translation Error: {e}]"


    async def get_summary_and_actions(self, texts: list[str], previous_summary: str) -> dict:
        """누적된 텍스트를 기반으로 요약과 액션 아이템 추출."""
        # TODO: (팀원 B) 이 함수를 배치 Worker에서 사용할 수 있도록 실제 LangChain RAG 로직 구현
        print(f"LLM Summary/AI Service: {len(texts)} chunks received. Waiting for implementation...")
        await asyncio.sleep(1)
        return {
            "rolling_summary": f"{previous_summary}\n- New discussion point added.",
            "action_items": []
        }