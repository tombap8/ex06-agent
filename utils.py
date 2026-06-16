import os 
from openai import AsyncOpenAI, OpenAI
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 불러옵니다. (주로 OPENAI_API_KEY 등의 비밀키 설정에 사용됨)
load_dotenv()

# 동기(Synchronous) API 호출을 위한 OpenAI 클라이언트 인스턴스 생성
client = OpenAI() 

# 비동기(Asynchronous) API 호출을 위한 OpenAI 클라이언트 인스턴스 생성
async_client = AsyncOpenAI()

# 동기 방식으로 LLM(대형 언어 모델)을 호출하는 함수
# prompt: 사용자 질문 또는 시스템 지시어
# model: 사용할 모델 이름 (기본값은 "gpt-4o")
def llm_call(prompt: str, model: str = "gpt-4o") -> str:
    # OpenAI API에 텍스트 생성을 요청합니다.
    response = client.chat.completions.create(
        model=model, 
        messages=[{"role": "user", "content": prompt}]
    )
    # 응답 데이터 구조에서 실제 텍스트 메시지만 추출하여 반환합니다.
    return response.choices[0].message.content

# 비동기 방식으로 LLM을 호출하는 함수 (병렬 처리 등에 유리함)
# async/await 키워드를 사용하여 호출 완료를 기다립니다.
async def llm_call_async(prompt: str, model: str = "gpt-4o") -> str:
    # 비동기 클라이언트를 통해 API 요청을 보내고 결과를 기다립니다. (이 동안 다른 비동기 작업 실행 가능)
    response = await async_client.chat.completions.create(
        model=model, 
        messages=[{"role": "user", "content": prompt}]
    )
    # 응답 데이터 구조에서 실제 텍스트 메시지만 추출하여 반환합니다.
    return response.choices[0].message.content
