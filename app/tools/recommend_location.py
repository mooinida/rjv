import math
import asyncio
from langchain_core.tools import tool

from service.saveRestaurant_pipeline import (
    get_location_from_text,
    get_coordinates_from_location,
    get_nearby_restaurants_DB
)
from service.review_fetch import get_review_texts
from llm.gemini_call import run_llm_analysis, get_final_recommendation
import time


@tool
async def recommend_by_location(text: str):
    """
    사용자의 지역 기반 입력을 바탕으로, 해당 지역에서 리뷰 수와 평점이 높은 인기 식당을 선별하고, 리뷰를 AI로 분석해 최종 추천하는 인기 식당 추천 도구입니다.
    """
    start = time.time()
    location = get_location_from_text(text)

    coords = get_coordinates_from_location(location)
    if "error" in coords:
        return coords

    restaurants_data = get_nearby_restaurants_DB(coords["latitude"], coords["longitude"], radius=350)
    
    if not restaurants_data or restaurants_data.get("restaurants") is None:
        return {"error": "식당 데이터를 불러오지 못했습니다."}
    
    filtered_restaurants = [
        r for r in restaurants_data["restaurants"]
            if r.get("reviewCount", 0) >= 5
    ]
    for r in filtered_restaurants:
        rating = r.get("rating", 0)
        review_count = r.get("reviewCount", 0)
        score = 0.6 * rating + 0.4 * math.log(review_count + 1)
        r["score"] = score
    
    top_restaurants = sorted(filtered_restaurants, key=lambda r: r["score"], reverse=True)[:10]
    
    ai_rating = await run_llm_analysis(top_restaurants)

    results = await get_final_recommendation(ai_rating)
    end = time.time()
    print(f"⏱️ 처리 시간: {end - start:.2f}초") 
    return results

    


    
