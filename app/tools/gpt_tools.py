# tools/gpt_tools.py

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio

# 수정된 '목표' 버전의 서비스 함수들을 임포트합니다.
from service.saveRestaurant_pipeline import (
    get_location_and_context,
    get_location_and_menu,
    get_coordinates_from_location,
    get_location_from_text,
    get_nearby_restaurants_DB,
    filtering_restaurant # 점수 기반 필터링 함수 추가
)
from bring_to_server import (
    bring_menu_filter_restaurants,
    bring_context_filter_restaurants,
    bring_restaurants_list,
    bring_rating_count # 리뷰 수/평점만 가져오는 함수 추가
)
from llm.gemini_call import run_llm_analysis, get_final_recommendation
from typing import TypedDict
from langgraph.graph import StateGraph

# LangGraph 호환 도구 함수들

# ✅ user_id 인자를 받도록 모든 도구 함수들의 정의를 수정합니다.
async def get_location_tool(user_id: str, input_text: str) -> dict:
    print("locationTool 사용")
    location = await get_location_from_text(input_text)
    coords = await get_coordinates_from_location(location)
    if "error" in coords:
        return coords
    # user_id를 사용해 DB에서 식당 정보를 가져옵니다.
    restaurants = get_nearby_restaurants_DB(user_id, coords["latitude"], coords["longitude"], radius=500)
    return restaurants

async def get_menu_tool(user_id: str, input_text: str) -> dict:
    print("getmenuTool 사용")
    keywords = await get_location_and_menu(input_text)
    # user_id를 사용해 DB에서 필터링합니다.
    restaurants = bring_menu_filter_restaurants(user_id, keywords)
    return restaurants

async def get_context_tool(user_id: str, input_text: str) -> dict:
    print("getcontextTool 사용")
    contexts = await get_location_and_context(input_text)
    # user_id를 사용해 DB에서 필터링합니다.
    restaurants = bring_context_filter_restaurants(user_id, contexts)
    return restaurants

# ✅ 더 정교한 교집합 로직으로 변경
def intersection_restaurant(location: dict, menu: dict, context: dict) -> dict:
    """
    여러 리스트의 교집합을 찾되, 결과가 너무 적으면 단계적으로 완화하는 도구.
    """
    print("교집합 함수 호출")
    try:
        location_ids = set(location.get("restaurants", []))
        menu_ids = set(menu.get("restaurants", []))
        context_ids = set(context.get("restaurants", []))

        # 1. 세 조건 모두 만족 (가장 정확)
        if location_ids and menu_ids and context_ids:
            lmc_intersection = list(location_ids & menu_ids & context_ids)
            if len(lmc_intersection) >= 3:
                print(f"✅ 3요소 교집합 사용: {len(lmc_intersection)}개")
                return {"restaurants": lmc_intersection}

        # 2. 위치 + 메뉴 또는 위치 + 컨텍스트 만족
        lm_intersection = list(location_ids & menu_ids)
        lc_intersection = list(location_ids & context_ids)
        
        if len(lm_intersection) >= 5 or len(lc_intersection) >= 5:
            combined = list(set(lm_intersection + lc_intersection))
            print(f"✅ 2요소 교집합 사용: {len(combined)}개")
            return {"restaurants": combined}

        # 3. 위 조건들을 만족하는 식당이 너무 없으면 위치 기반으로만 추천
        print(f"⚠️ 교집합 결과가 너무 적어 위치 기반으로만 추천합니다.")
        return {"restaurants": list(location_ids)}

    except Exception as e:
        return {"error": str(e)}

# ✅ 점수 기반 필터링 단계 추가
def get_restaurant_info(user_id: str, restaurant_ids: dict) -> dict:
    """
    교집합으로 나온 후보 식당 ID를 받아, 평점/리뷰 수로 1차 필터링 후,
    상세 정보를 가져오는 도구.
    """
    print("상세 정보 조회 및 필터링 함수 호출")
    try:
        candidates = restaurant_ids.get("restaurants", [])
        if not candidates:
            return {"restaurants": []}
            
        # 1. 평점, 리뷰 수만 먼저 가져와서 점수 계산 후 필터링
        rating_data = bring_rating_count(user_id, candidates)
        top_10_ids = filtering_restaurant(rating_data) # 상위 10개 식당 ID 추출

        # 2. 필터링된 상위 10개 식당의 전체 상세 정보 요청
        final_details = bring_restaurants_list(user_id, top_10_ids)
        return final_details
    except Exception as e:
        print(f"상세 정보 조회 중 오류: {e}")
        return {"error": f"상세 정보를 조회하는 중 오류 발생: {str(e)}"}

async def final_recommend(restaurants_info: dict, input_text: str) -> dict:
    """LLM을 호출하여 최종 추천 문구를 생성합니다."""
    # run_llm_analysis는 이제 사용하지 않고, get_final_recommendation만 사용합니다.
    # get_final_recommendation이 JSON 리스트를 직접 반환합니다.
    result = await get_final_recommendation(restaurants_info, input_text)
    return result
