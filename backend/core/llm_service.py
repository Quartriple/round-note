import os
import json
from openai import AsyncOpenAI
import asyncio
from dotenv import load_dotenv

load_dotenv()

# 환경 변수에서 OpenAI API 키 로드
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# LLM 담당 팀원이 이 함수들을 구현하게 됩니다.

async def get_translation(text: str) -> str:
    """
    실시간으로 텍스트를 번역하는 코어 함수.
    (streaming_way_DG.py의 translation_thread 로직 재활용)
    """
    if not text.strip():
        return ""
        
    try:
        # streaming_way_DG.py에서 사용한 모델과 프롬프트 재현
        chat_completion = await client.chat.completions.create(
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


async def get_summary_and_actions(texts: list[str], previous_summary: str) -> dict:
    """
    누적된 텍스트를 기반으로 요약과 액션 아이템을 추출하는 코어 함수.
    (streaming_way_DG.py의 summary_thread 로직 재활용)
    """
    # 이 부분은 배치 처리 파이프라인에서 구현이 필요하므로, 현재는 더미 데이터로 대체합니다.
    # LLM 팀원이 이 함수의 내부 로직을 담당하게 됩니다.
    print(f"LLM Summary/AI Service: {len(texts)} chunks received. Waiting for implementation...")
    await asyncio.sleep(1) # 비동기 API 호출 흉내
    return {
        "rolling_summary": f"{previous_summary}\n- New discussion point added.",
        "action_items": []
    }