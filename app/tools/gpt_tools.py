# tools/gpt_tools.py

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio

# LLM 호출 로직
from llm.gemini_call import get_final_recommendation

# ★★★ 수정된 bring_to_server에서 함수들을 가져옵니다. ★★★
from bring_to_server import (
    bring_menu_filter_restaurants,
    bring_context_filter_restaurants,
    bring_restaurants_list,
    bring_rating_count
)
# ★★★ 수정된 saveRestaurant_pipeline에서 함수들을 가져옵니다. ★★★
from service.saveRestaurant_pipeline import (
    get_location_and_context,
    get_location_and_menu,
    get_coordinates_from_location,
    get_location_from_text,
    filtering_restaurant
)


# ★★★ user_id 인자를 모두 제거합니다. ★★★
async def get_location_tool(input_text: str) -> dict:
    print("locationTool 사용")
    location = await get_location_from_text(input_text)
    coords = await get_coordinates_from_location(location)
    if "error" in coords:
        return coords
    
    # 더 이상 get_nearby_restaurants_DB를 직접 쓰지 않고,
    # bring_to_server의 함수들을 조합해서 사용하도록 로직을 가정할 수 있으나,
    # 지금은 해당 함수가 없으므로 일단 이 노드는 위치기반 식당을 가져오는 역할은 하지 않는다고 가정하거나,
    # 혹은 bring_to_server에 get_nearby_restaurants_DB 함수를 추가해야 합니다.
    # 일단은 빈 데이터를 반환하도록 임시 수정합니다. 실제 구현에서는 이 부분을 채워야 합니다.
    # 또는, 이 노드의 역할을 재정의해야 합니다.
    # 여기서는 임시로 빈 restaurant 리스트를 반환하도록 수정합니다.
    # 이 부분은 프로젝트의 정확한 로직에 따라 수정이 필요합니다.
    # 지금은 다른 노드와의 연계를 위해 임시로 placeId만 반환하는 형태로 가정하겠습니다.
    # 이 부분은 실제 Spring API에 따라 변경되어야 합니다.
    from bring_to_server import bring_nearby_restaurants # 예시 함수
    restaurants = bring_nearby_restaurants(coords["latitude"], coords["longitude"], radius=500)
    return restaurants

async def get_menu_tool(input_text: str) -> dict:
    print("getmenuTool 사용")
    keywords = await get_location_and_menu(input_text)
    restaurants = bring_menu_filter_restaurants(keywords)
    return restaurants

async def get_context_tool(input_text: str) -> dict:
    print("getcontextTool 사용")
    contexts = await get_location_and_context(input_text)
    restaurants = bring_context_filter_restaurants(contexts)
    return restaurants

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
        
# intersection_restaurant, final_recommend 함수는 user_id가 없으므로 그대로 둡니다.
def intersection_restaurant(location: dict, menu: dict, context: dict) -> dict:
    # ... (기존의 정교한 교집합 로직 그대로) ...

async def final_recommend(restaurants_info: dict, input_text: str) -> dict:
    # ... (기존 코드 그대로) ...
