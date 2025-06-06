from langchain_core.tools import tool

from service.saveRestaurant_pipeline import (
    get_location_and_menu,
    get_coordinates_from_location,
    get_nearby_restaurants_DB
)
from service.get_menu import get_menu_texts
from llm.gemini_call import run_llm_analysis, get_final_recommendation
from bring_to_server import bring_menu_filter_restaurants 
import time


@tool
async def recommend_by_menu(text: str):
    """
        사용자 입력에서 메뉴 또는 음식 카테고리를 추출하여,
        해당 키워드에 기반한 음식점을 검색하고 추천하는 함수입니다.
    """
    location, keywords= get_location_and_menu(text)
    print(keywords)
    coords = get_coordinates_from_location(location)
    if "error" in coords:
        return coords

    restaurants_data = get_nearby_restaurants_DB(coords["latitude"], coords["longitude"], radius = 500)
    

    if not restaurants_data or restaurants_data.get("restaurants") is None:
        return {"error": "식당 데이터를 불러오지 못했습니다."}
    
    restaurant_list = restaurants_data["restaurants"]
    place_id_list = [int(r["placeId"]) for r in restaurant_list]
    restaurants = bring_menu_filter_restaurants(place_id_list, keywords)
    ai_rating = await run_llm_analysis(restaurants)

    results = await get_final_recommendation(ai_rating)
    return results

    

    