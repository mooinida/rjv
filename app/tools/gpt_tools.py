# app/tools/gpt_tools.py

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio

from llm.gemini_call import get_final_recommendation
from service.saveRestaurant_pipeline import (
    get_location_and_context,
    get_location_and_menu,
    get_coordinates_from_location,
    get_location_from_text,
    filtering_restaurant
)
from bring_to_server import (
    bring_nearby_restaurants,
    bring_menu_filter_restaurants,
    bring_context_filter_restaurants,
    bring_restaurants_list,
    bring_rating_count
)

async def get_location_tool(input_text: str) -> dict:
    print("locationTool 사용")
    location = await get_location_from_text(input_text)
    if not location:
        return {"restaurants": []}
    coords = await get_coordinates_from_location(location)
    if "error" in coords:
        return coords
    restaurants = bring_nearby_restaurants(coords["latitude"], coords["longitude"], radius=500)
    return restaurants

async def get_menu_tool(input_text: str) -> dict:
    print("getmenuTool 사용")
    keywords = await get_location_and_menu(input_text)
    if not keywords:
        return {"restaurants": []}
    restaurants = bring_menu_filter_restaurants(keywords)
    return restaurants

async def get_context_tool(input_text: str) -> dict:
    print("getcontextTool 사용")
    contexts = await get_location_and_context(input_text)
    if not contexts:
        return {"restaurants": []}
    restaurants = bring_context_filter_restaurants(contexts)
    return restaurants

def intersection_restaurant(location: dict, menu: dict, context: dict) -> dict:
    print("교집합 함수 호출")
    try:
        location_ids = set(r['placeId'] for r in location.get("restaurants", []))
        menu_ids = set(r['placeId'] for r in menu.get("restaurants", []))
        context_ids = set(r['placeId'] for r in context.get("restaurants", []))

        # 메뉴나 컨텍스트 키워드가 없었을 경우, 해당 집합을 전체 식별자 집합으로 간주하여 교집합에 영향을 주지 않도록 함
        if not menu.get("restaurants"):
            menu_ids = location_ids.copy()
        if not context.get("restaurants"):
            context_ids = location_ids.copy()

        lmc_intersection = list(location_ids & menu_ids & context_ids)
        if len(lmc_intersection) >= 3:
            print(f"✅ 3요소 교집합 사용: {len(lmc_intersection)}개")
            return {"restaurants": lmc_intersection}

        lm_intersection = list(location_ids & menu_ids)
        lc_intersection = list(location_ids & context_ids)
        
        combined = list(set(lm_intersection + lc_intersection))
        if len(combined) >= 3:
            print(f"✅ 2요소 교집합 사용: {len(combined)}개")
            return {"restaurants": combined}

        print(f"⚠️ 교집합 결과가 너무 적어 위치 기반으로만 추천합니다: {len(location_ids)}개")
        return {"restaurants": list(location_ids)}

    except Exception as e:
        return {"error": str(e)}

def get_restaurant_info(restaurant_ids: dict) -> dict:
    print("상세 정보 조회 및 필터링 함수 호출")
    try:
        candidates = restaurant_ids.get("restaurants", [])
        if not candidates:
            return {"restaurants": []}
            
        rating_data = bring_rating_count(candidates)
        top_10_ids = filtering_restaurant(rating_data)
        final_details = bring_restaurants_list(top_10_ids)
        return final_details
    except Exception as e:
        print(f"상세 정보 조회 중 오류: {e}")
        return {"error": f"상세 정보를 조회하는 중 오류 발생: {str(e)}"}

async def final_recommend(restaurants_info: dict, input_text: str) -> list:
    result = await get_final_recommendation(restaurants_info, input_text)
    return result
