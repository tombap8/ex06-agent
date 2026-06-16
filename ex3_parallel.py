import asyncio

from utils import llm_call_async

# 여러 LLM API 호출을 병렬로 동시에 실행하는 함수
async def run_llm_parallel(prompt_details):
    # 각 프롬프트(질문)와 지정된 모델에 대해 비동기 태스크(작업) 리스트를 생성합니다.
    tasks = [llm_call_async(prompt['user_prompt'], prompt['model']) for prompt in prompt_details]
    responses = []
    
    # asyncio.as_completed를 사용하여 병렬로 실행된 작업 중 먼저 완료되는 것부터 순차적으로 결과를 처리합니다.
    for task in asyncio.as_completed(tasks):
        result = await task
        print("LLM 응답 완료:", result)
        responses.append(result)
        
    
    return responses

# 비동기 메인 함수
async def main():
    question = ("아래 문장을 자연스러운 한국어로 번역해줘:\n"
                "\"Do what you can, with what you have, where you are.\" — Theodore Roosevelt")
    
    # 동일한 질문을 3가지 다른 모델(gpt-4o, gpt-4o-mini, gpt-3.5-turbo)에 병렬로 던지기 위한 설정입니다.
    # 이를 통해 각 모델의 다양한 해석을 동시에 빠르게 얻어낼 수 있습니다.
    parallel_prompt_details = [
        {"user_prompt": question, "model": "gpt-4o"},
        {"user_prompt": question, "model": "gpt-4o-mini"},
        {"user_prompt": question, "model": "gpt-3.5-turbo"},
    ]
    
    # 설정된 3개의 작업을 병렬로 실행하여 응답을 수집합니다.
    responses = await run_llm_parallel(parallel_prompt_details)
    
    # 병렬로 수집된 여러 모델의 응답을 하나로 모아 평가하고 종합(Aggregator)하기 위한 프롬프트입니다.
    aggregator_prompt = ("다음은 여러 개의 AI 모델이 사용자 질문에 대해 생성한 응답입니다.\n"
                         "당신의 역할은 이 응답들을 모두 종합하여 최종 답변을 제공하는 것입니다.\n"
                         "일부 응답이 부정확하거나 편향될 수 있으므로, 신뢰성과 정확성을 갖춘 응답을 생성하는 것이 중요합니다.\n\n"
                         "사용자 질문:\n"
                         f"{question}\n\n"
                         "모델 응답들:")
    
    # 앞서 병렬 처리로 수집한 개별 응답들을 종합 프롬프트에 차례대로 추가합니다.
    for i in range(len(parallel_prompt_details)):
        aggregator_prompt += f"\n{i+1}. 모델 응답: {responses[i]}\n"
    
    print("---------------------------종합 프롬프트:-----------------------\n", aggregator_prompt)
    
    # 종합자(Aggregator) 역할을 수행하는 강력한 모델(gpt-4o)을 호출하여, 
    # 여러 응답의 장점을 바탕으로 검증되고 개선된 최적의 최종 답변을 생성합니다.
    final_response = await llm_call_async(aggregator_prompt, model="gpt-4o")
    print("---------------------------최종 종합 응답:-----------------------\n", final_response)

# 비동기 main 함수 실행 (프로그램 시작점)
asyncio.run(main())
