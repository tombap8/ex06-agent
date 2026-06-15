import os 
from openai import AsyncOpenAI, OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI() 
async_client = AsyncOpenAI()

def llm_call(prompt: str, model: str = "gpt-4o") -> str:
    response = client.chat.completions.create(
        model=model, 
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

async def llm_call_async(prompt: str, model: str = "gpt-4o") -> str:
    response = await async_client.chat.completions.create(
        model=model, 
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
