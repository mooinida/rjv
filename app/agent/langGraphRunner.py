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
class State(TypedDict):
    user_id: str
    user_input: str
    location: dict
    menu: dict
    context: dict
    candidates: dict          
    restaurant_details: dict  
    result: list
    end: bool

# --- 노드 함수 (Node Functions) ---
async def extract_all(state: State) -> dict:
    try:
        user_id = state["user_id"]
        user_input = state["user_input"]
        
        location_task = get_location_tool(user_id, user_input)
        menu_task = get_menu_tool(user_id, user_input)
        context_task = get_context_tool(user_id, user_input)

        location, menu, context = await asyncio.gather(
            location_task, menu_task, context_task, return_exceptions=True
        )
        
        if not location.get("restaurants"):
            return {
                "end": True,
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
    candidates = intersection_restaurant(
        state["location"],
        state["menu"],
        state["context"]
    )
    return {"candidates": candidates}

async def detail_node(state: State) -> dict:
    details = get_restaurant_info(state["user_id"], state["candidates"])
    return {"restaurant_details": details}

async def final_node(state: State) -> dict:  
    result_list = await final_recommend(state["restaurant_details"], state["user_input"])
    return {"result": result_list}

# --- 조건부 엣지 (Conditional Edge) ---

# ★★★ 1차 수정: END 객체 대신 "__end__" 문자열을 반환하도록 변경 ★★★
def next_tool_selector(state: dict) -> str:
    """extract_all 노드 이후 분기점을 결정합니다."""
    if state.get("end") is True:
        return "__end__"
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


# ★★★ 2차 수정: 매핑 딕셔너리를 세 번째 인자로 추가 ★★★
graph_builder.add_conditional_edges(
    "extract_filters",      # 1. 시작 노드
    next_tool_selector,     # 2. 조건부 함수
    {                       # 3. 매핑 (어떤 문자열이 반환될 때, 어떤 노드로 갈지 정의)
        "intersection_node": "intersection_node",
        "__end__": END
    }
)

# 나머지 엣지 연결
graph_builder.add_edge("intersection_node", "detail_node")
graph_builder.add_edge("detail_node", "final_node")
graph_builder.add_edge("final_node", END)

# --- 실행 함수 (Executor) ---
async def run_recommendation_pipeline(state: dict) -> dict:
    """정의된 LangGraph를 컴파일하고 실행합니다."""
    graph = graph_builder.compile()
    result = await graph.ainvoke(state)
    return result
