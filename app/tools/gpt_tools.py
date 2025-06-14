import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from service.saveRestaurant_pipeline import (
    get_location_and_context,
    get_location_and_menu,
    get_coordinates_from_location,
    get_location_from_text,
    get_nearby_restaurants_DB
)
from bring_to_server import (
    bring_menu_filter_restaurants,
    bring_context_filter_restaurants,
    bring_restaurants_list
)
from llm.gemini_call import run_llm_analysis, get_final_recommendation
from collections import Counter
from typing import TypedDict
from langgraph.graph import StateGraph

# Define the state structure
class State(TypedDict):
    user_input: str
    location: dict
    menu: dict
    context: dict
    candidates: dict
    restaurant_details: dict
    result: dict

# LangGraph-compatible tools

async def get_location_tool(input_text: str) -> dict:
    print("locationTool사용")
    location = get_location_from_text(input_text)
    coords = get_coordinates_from_location(location)
    if "error" in coords:
        return coords
    restaurants = get_nearby_restaurants_DB(coords["latitude"], coords["longitude"], radius=500)
    return restaurants


async def get_menu_tool(input_text: str) -> dict:
    print("getmenuTool사용")
    keywords = get_location_and_menu(input_text)
    restaurants = bring_menu_filter_restaurants(keywords)
    return restaurants


async def get_context_tool(input_text: str) -> dict:
    print("getcontextTool사용")
    contexts = get_location_and_context(input_text)
    restaurants = bring_context_filter_restaurants(contexts)
    return restaurants


def get_restaurant_info(restaurant_ids: dict) -> dict:
    print("정보가져오기 함수")
    try:
        restaurants = restaurant_ids.get("restaurants", [])
        data = bring_restaurants_list(restaurants)
        print(data)
        return data
    except Exception as e:
        return {"error": f"파싱 실패: {str(e)}"}


def intersection_restaurant(location:dict, menu:dict, context:dict):
    """
    여러 리스트에서 2번 이상 등장한 식당 ID만 반환하는 도구.
    """
    print("교집합함수 호출")
    try:
        location_ids = location.get("restaurants", [])
        menu_ids = menu.get("restaurants", [])
        context_ids = context.get("restaurants", [])

        all_ids = location_ids + menu_ids + context_ids
        counter = Counter(all_ids)

        # 2번 이상 등장하는 ID 필터링
        result = [rid for rid, count in counter.items() if count > 2]
        print(result)
        return {"restaurants": result}

    except Exception as e:
        return {"error": str(e)}

async def final_recommend(restaurants_info: dict, input_text:str) -> dict:
    ai_rating = await run_llm_analysis(restaurants_info)
    results = await get_final_recommendation(ai_rating, input_text)
    return results

graph_builder = StateGraph(State)

