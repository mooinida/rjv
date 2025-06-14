from service.prompt import build_review_prompt, build_final_recommendation_prompt
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
import asyncio
import json
import re

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-pro", google_api_key=GOOGLE_API_KEY)

async def call_llm(prompt: str, print_result: bool = False) -> str:
    result = await llm.ainvoke(prompt)
    if print_result:
        print("🔍 LLM 응답:", result.content)
    return result.content

async def analyze_restaurant(restaurant: dict) -> dict:
    prompt = build_review_prompt(restaurant)
    response = await call_llm(prompt)
    return {
        "placeId": restaurant["placeId"],
        "name": restaurant["name"],
        "url": restaurant["url"],
        "llmResult": response
    }

async def run_llm_analysis(data: dict) -> list:
    restaurants = data.get("restaurants", [])
    if not isinstance(restaurants, list):
        raise ValueError("'restaurants' 필드는 리스트여야 합니다.")
    return await asyncio.gather(*(analyze_restaurant(r) for r in restaurants))

async def get_final_recommendation(results: list, input_text: str) -> list:
    final_prompt = build_final_recommendation_prompt(results, input_text)
    response_text = await call_llm(final_prompt)
    print("📦 최종 추천 응답:", response_text)

    try:
        json_match = re.search(r"\[[\s\S]*\]", response_text)
        if not json_match:
            raise json.JSONDecodeError("JSON 배열을 찾을 수 없습니다.", response_text, 0)
        json_str = json_match.group(0)
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print("❌ JSON 파싱 실패:", e)
        return [{"error": "AI 응답 형식 오류로 추천 결과를 생성할 수 없습니다."}]
