import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_core.tools import tool
from service.saveRestaurant_pipeline import get_location_and_context,get_location_and_menu,get_coordinates_from_location,get_location_from_text,get_nearby_restaurants_DB
from bring_to_server import bring_menu_filter_restaurants, bring_context_filter_restaurants, bring_restaurants_list
from llm.gemini_call import run_llm_analysis, get_final_recommendation
import ast
from collections import Counter

accumulated_list = {}
added_tools = set()
restaurant_info_dict = {}


async def get_location_tool(input_text:str)->list:
    """
    사용자의 입력에서 지역을 뽑아내서 그 지역주변 식당의 id리스트를 받는 도구.
    """
    print("locationTool사용")
    location = get_location_from_text(input_text)
    coords = get_coordinates_from_location(location)
    if "error" in coords:
        return coords
    restaurants = get_nearby_restaurants_DB(coords["latitude"], coords["longitude"], radius=500)
    return restaurants


async def get_menu_tool(input_text:str) -> list:
    """
    사용자의 입력에서 메뉴가 있을 때, 그 메뉴를 판매하고 있는 식당의 id리스트를 받는 도구.
    """
    print("getmenuTool사용")
    keywords= get_location_and_menu(input_text)
    restaurants = bring_menu_filter_restaurants(keywords)
    return restaurants


async def get_context_tool(input_text:str):
    """
    사용자의 입력에서 그 식당의 상황(예: 혼밥, 회식), 분위기(예: 조용한, 감성적인), 목적(예: 데이트, 가볍게 한잔)같은 조건에 해당하는 식당의 id리스트를 받는 도구.
    """
    print("getcontextTool사용")
    contexts = get_location_and_context(input_text)
    restaurants = bring_context_filter_restaurants(contexts)
    return restaurants


def get_restaurant_info(restaurant_ids:dict):
    """
    식당 id를 사용하여 상세 정보(리뷰, 주소 등)를 조회하는 도구.
    """
    try:
        restaurants = restaurant_ids.get("restaurants",[])
        data  = bring_restaurants_list(restaurants)
        return data
    except Exception as e:
        return {"error": f"파싱 실패: {str(e)}"}

def intersection_restaurant(location:list, menu:list, context:list):
    """
    여러 리스트에서 2번 이상 등장한 식당 ID만 반환하는 도구.
    """
    try:
        # 모든 리스트 합치기
        all_ids = location + menu + context
        counter = Counter(all_ids)

        # 2번 이상 등장하는 ID 필터링
        result = [rid for rid, count in counter.items() if count > 1]

        return {"restaurants": result}

    except Exception as e:
        return {"error": str(e)}


async def final_recommend(restaurantsInfo:dict):
    """
    최종적으로 식당을 선택하여 추천하는도구.
    """
    ai_rating = await run_llm_analysis(restaurantsInfo)
    results = await get_final_recommendation(ai_rating)
    return results

@tool
async def search_restaurants(user_input: str) -> dict:
    """
    사용자의 질문에 적합한 식당을 추천하는 함수.
    """
    location_result = await get_location_tool(user_input)
    menu_result =await get_menu_tool(user_input)
    context_result =await get_context_tool(user_input)

    candidates = intersection_restaurant(
        location_result.get("restaurants", []),
        menu_result.get("restaurants", []),
        context_result.get("restaurants", [])
)
    print(candidates)
    restaurants_detail = get_restaurant_info(candidates)    
    result = await final_recommend(restaurants_detail)
    return result

