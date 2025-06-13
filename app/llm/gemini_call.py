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

async def call_llm(prompt: str):
    result = await llm.ainvoke(prompt)
    return result.content

async def analyze_restaurant(restaurant: dict) -> dict:
    prompt = build_review_prompt(restaurant)
    response_content = await call_llm(prompt)
    return {
        "name": restaurant.get("name"),
        "reason": response_content, # AI가 생성한 추천 이유
        "actualRating": str(restaurant.get("rating", "0.0")), # 실제 평점은 원래 데이터 사용
    }

async def run_llm_analysis(data: dict) -> list:
    restaurants = data.get("restaurants", [])
    if not isinstance(restaurants, list):
        raise ValueError("restaurants는 리스트여야 합니다.")
    tasks = [analyze_restaurant(r) for r in restaurants]
    return await asyncio.gather(*tasks)

# ✅✅✅ 이 함수가 핵심적인 수정 부분입니다. ✅✅✅
async def get_final_recommendation(analyzed_restaurants: list, input_text: str) -> list:
    """
    1차 분석된 레스토랑 목록과 사용자 요청을 바탕으로 최종 추천 목록을 생성합니다.
    AI에게는 점수만 매기도록 하고, 파이썬에서 데이터를 최종 조합합니다.
    """
    final_prompt = build_final_recommendation_prompt(analyzed_restaurants, input_text)
    response_text = await call_llm(final_prompt)
    print("AI 최종 점수 응답:", response_text)

    try:
        # AI가 매긴 점수 데이터를 파싱합니다. ex: {"The Cozy Bistro": "4.8", ...}
        scores_data = json.loads(response_text)
        
        # 원본 데이터에 AI 평점을 추가하고 점수 순으로 정렬합니다.
        for restaurant in analyzed_restaurants:
            # AI가 매긴 점수가 있으면 해당 점수를, 없으면 0점을 부여합니다.
            ai_score = scores_data.get(restaurant["name"], "0.0")
            restaurant["aiRating"] = ai_score

        # aiRating을 기준으로 내림차순 정렬합니다.
        sorted_restaurants = sorted(
            analyzed_restaurants, 
            key=lambda r: float(r.get("aiRating", 0.0)), 
            reverse=True
        )
        
        # 상위 5개만 반환합니다.
        return sorted_restaurants[:5]

    except (json.JSONDecodeError, TypeError) as e:
        print(f"❌ 최종 추천 결과 파싱 또는 정렬 실패: {e}")
        # 실패 시, 그냥 1차 분석 결과라도 반환합니다.
        return analyzed_restaurants[:5]
