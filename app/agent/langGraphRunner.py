# agent/langGraphRunner.py

import os
import sys
import asyncio

# 프로젝트 루트 경로를 sys.path에 추가하여 다른 모듈을 임포트할 수 있도록 함
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langgraph.graph import StateGraph, END
from typing import TypedDict
from langchain_core.runnables import RunnableLambda

# 'after' 아키텍처에 맞는 gpt_tools의 함수들을 임포트
from tools.gpt_tools import (
    get_location_tool,
    get_menu_tool,
    get_context_tool,
    intersection_restaurant,
    get_restaurant_info,
    final_recommend,
)

# --- 상태 정의 (State Definition) ---
# user_id를 포함하여 인증 및 데이터 조회에 사용
class State(TypedDict):
    user_id: str
    user_input: str
    location: dict
    menu: dict
    context: dict
    candidates: dict          
    restaurant_details: dict  
    result: list # 최종 결과는 이제 JSON 객체의 리스트
    end: bool # 그래프를 조기 종료하기 위한 플래그

# --- 노드 함수 (Node Functions) ---

# ✅ 성능 개선: 위치, 메뉴, 컨텍스트를 병렬로 추출하는 노드
async def extract_all(state: State) -> dict:
    """사용자 입력에서 위치, 메뉴, 컨텍스트 정보를 병렬로 추출합니다."""
    try:
        user_id = state["user_id"]
        user_input = state["user_input"]
        
        # 세 가지 정보 추출 작업을 동시에 실행
        location_task = get_location_tool(user_id, user_input)
        menu_task = get_menu_tool(user_id, user_input)
        context_task = get_context_tool(user_id, user_input)

        location, menu, context = await asyncio.gather(
            location_task, menu_task, context_task, return_exceptions=True
        )
        
        # 위치 정보가 없는 경우, 추천을 진행할 수 없으므로 그래프를 종료
        if not location.get("restaurants"):
            return {
                "end": True, # 종료 플래그 설정
                "result": [{"error": "장소명을 인식할 수 없습니다. 더 자세한 장소명과 함께 다시 질문해주세요."}]
            }

        return {
            "location": location,
            "menu": menu,
            "context": context
        }
    except Exception as e:
        print(f"❌ extract_all 노드에서 에러 발생: {e}")
        return {"end": True, "result": [{"error": "정보를 추출하는 중 오류가 발생했습니다."}]}

async def intersection_node(state: State) -> dict:
    """추출된 정보를 바탕으로 교집합 식당을 찾습니다."""
    candidates = intersection_restaurant(
        state["location"],
        state["menu"],
        state["context"]
    )
    return {"candidates": candidates}

async def detail_node(state: State) -> dict:
    """후보 식당들의 상세 정보를 가져옵니다."""
    details = get_restaurant_info(state["user_id"], state["candidates"])
    return {"restaurant_details": details}

async def final_node(state: State) -> dict:  
    """최종 추천 결과를 생성합니다."""
    # final_recommend는 이제 JSON 객체의 리스트를 반환
    result_list = await final_recommend(state["restaurant_details"], state["user_input"])
    return {"result": result_list}

# --- 조건부 엣지 (Conditional Edge) ---
def next_tool_selector(state: dict) -> str:
    """extract_all 노드 이후 분기점을 결정합니다."""
    if state.get("end") is True:
        # end 플래그가 설정되었다면 그래프를 종료
        return END
    # 그렇지 않으면 교집합 노드로 진행
    return "intersection_node"

# --- 그래프 구성 (Graph Construction) ---
graph_builder = StateGraph(State)

# 노드 등록
graph_builder.add_node("extract_filters", RunnableLambda(extract_all))
graph_builder.add_node("intersection_node", intersection_node)
graph_builder.add_node("detail_node", detail_node)
graph_builder.add_node("final_node", final_node)

# 그래프 진입점 설정
graph_builder.set_entry_point("extract_filters")

# 엣지 연결
graph_builder.add_conditional_edges(
    "extract_filters", # 시작 노드
    next_tool_selector # 조건부 함수
    # 이 함수가 반환하는 문자열에 따라 다음 노드가 결정됨
    # "intersection_node" 또는 END
)
graph_builder.add_edge("intersection_node", "detail_node")
graph_builder.add_edge("detail_node", "final_node")
graph_builder.add_edge("final_node", END) # final_node 이후 그래프 종료

# --- 실행 함수 (Executor) ---
async def run_recommendation_pipeline(state: dict) -> dict:
    """정의된 LangGraph를 컴파일하고 실행합니다."""
    graph = graph_builder.compile()
    result = await graph.ainvoke(state)
    return result
