from langchain_core.tools import tool
from service.saveRestaurant_pipeline import (
    get_location_and_context,
    get_coordinates_from_location,
    get_nearby_restaurants_DB
)
from llm.gemini_call import run_llm_analysis, get_final_recommendation
from bring_to_server import bring_context_filter_restaurants 
@tool
async def recommend_by_context(text: str):
    """
    사용자의 입력에서 상황(예: 혼밥, 회식), 분위기(예: 조용한, 감성적인), 목적(예: 데이트, 가볍게 한잔)을 추출하고,
    해당 키워드와 식당 리뷰를 비교하여 적합한 식당을 추천하는 함수입니다.
    """
    location, keywords= get_location_and_context(text)
    print(keywords)
    coords = get_coordinates_from_location(location)
    if "error" in coords:
        return coords

    restaurants_data = get_nearby_restaurants_DB(coords["latitude"], coords["longitude"], radius = 500)
    

    if not restaurants_data or restaurants_data.get("restaurants") is None:
        return {"error": "식당 데이터를 불러오지 못했습니다."}
    
    restaurant_list = restaurants_data["restaurants"]
    place_id_list = [int(r["placeId"]) for r in restaurant_list]
    restaurants = bring_context_filter_restaurants (place_id_list, keywords)
    ai_rating = await run_llm_analysis(restaurants)

    results = await get_final_recommendation(ai_rating)
    return results

    