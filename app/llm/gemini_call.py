from service.prompt import build_review_prompt, build_final_recommendation_prompt
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
import asyncio
JWT_TOKEN = os.getenv("JWT_TOKEN")
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-pro", google_api_key=GOOGLE_API_KEY, model_kwargs={"streaming": True})

async def call_llm(prompt: str, print_result: bool):
    stream = llm.astream(prompt)
    result = ""
    async for chunk in stream:
        if chunk.content:
            result += chunk.content
    if print_result:
        print()
    return result

async def analyze_restaurant(restaurant: dict) -> dict:
    prompt = build_review_prompt(restaurant)
    response =await call_llm(prompt, print_result=False)
    result = {
        "placeId": restaurant["placeId"],
        "name": restaurant["name"],
        "url": restaurant["url"],
        "llmResult": response
    }
    return result
async def run_llm_analysis(data: dict) -> list:
    restaurants = data.get("restaurants", [])
    if not isinstance(restaurants, list):
        raise ValueError("restaurants는 리스트여야 합니다.")

    tasks = [analyze_restaurant(r) for r in restaurants]
    return await asyncio.gather(*tasks)


async def get_final_recommendation(results: list, input_text:str) -> str:
    """
    전체 흐름: 개별 분석 → 종합 프롬프트 → 최종 추천 생성
    """
    final_prompt = build_final_recommendation_prompt(results, input_text)
    return await call_llm(final_prompt, print_result = True)
