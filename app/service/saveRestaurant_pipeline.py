# service/saveRestaurant_pipeline.py

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
import json
import re
import os
import math
from dotenv import load_dotenv
import aiohttp # get_coordinates_from_location에 필요

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-pro", google_api_key=GOOGLE_API_KEY)

# --- 정보 추출 함수들 (LLM 호출) ---
# 이 부분은 이전과 동일하게 유지합니다.
async def get_location_and_context(text: str):
    # ... (기존 코드 그대로) ...
async def get_location_and_menu(text: str):
    # ... (기존 코드 그대로) ...
async def get_location_from_text(text: str) -> str:
    # ... (기존 코드 그대로) ...
async def get_coordinates_from_location(location: str):
    # ... (기존 코드 그대로) ...

# ★★★ 여기서부터 수정 ★★★
# DB 연동 및 my_token 관련 함수들을 모두 제거하고, filtering_restaurant 함수만 남깁니다.

def filtering_restaurant(restaurants: dict) -> list[int]:
    """
    평점과 리뷰 수를 기반으로 식당의 점수를 매기고,
    상위 10개 식당의 placeId 리스트를 반환합니다.
    """
    filtered_restaurants = []
    
    for r in restaurants.get("restaurants", []):
        try:
            if int(r.get("reviewCount", 0)) >= 1:
                filtered_restaurants.append(r)
        except (ValueError, TypeError):
            continue
    
    for r in filtered_restaurants:
        try:
            rating = float(r.get("rating", 0))
            review_count = int(r.get("reviewCount", 0))
            score = 0.6 * rating + 0.4 * math.log(review_count + 1)
            r["score"] = score
        except (ValueError, TypeError):
            r["score"] = 0
    
    top_restaurants = sorted(filtered_restaurants, key=lambda r: r.get("score", 0), reverse=True)[:10]
    
    place_ids = [r["placeId"] for r in top_restaurants]
    return place_ids
