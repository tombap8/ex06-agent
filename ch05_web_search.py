import os
import asyncio
from openai import AsyncOpenAI

# .env 파일 로드 : 설정된 OPENAI_API_KEY를 불러옴
from dotenv import load_dotenv
load_dotenv()

# OpenAI API 키 설정 : OPENAI_API_KEY를 async_client에 전달
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
async_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# 웹 검색 기능을 포함한 LLM 호출 함수 선언
async def llm_search_async(prompt: str, model: str = "gpt-4o") -> str:
    response = await async_client.responses.create(
        model = model,
        input = prompt,
        tools = [{"type": "web_search_preview"}],
    )
    return response.output_text

# 메인 함수 선언 및 실행
async def main():
    prompt = "오늘의 흥미로운 뉴스를 찾아줘."
    result = await llm_search_async(prompt)
    print("\n 웹 검색 결과:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())