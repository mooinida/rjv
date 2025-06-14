# app/agent/langGraphRunner.py

import os
import sys
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langgraph.graph import StateGraph, END
from typing import TypedDict
from langchain_core.runnables import RunnableLambda

from tools.gpt_tools import (
    get_location_tool,
    get_menu_tool,
    get_context_tool,
    intersection_restaurant,
    get_restaurant_info,
    final_recommend,
)

class State(TypedDict):
    user_input: str
    location: dict
    menu: dict
    context: dict
    candidates: dict          
    restaurant_details: dict  
    result: list
    end: bool

async def extract_all(state: State) -> dict:
    try:
        user_input = state["user_input"]
        
        location_task = get_location_tool(user_input)
        menu_task = get_menu_tool(user_input)
        context_task = get_context_tool(user_input)

        location, menu, context = await asyncio.gather(
            location_task, menu_task, context_task, return_exceptions=True
        )
        
        # is_empty와 같은 별도 키 대신, 레스토랑 리스트가 비었는지 직접 확인
        if not location.get("restaurants"):
            return {
                "end": True,
                "result": [{"error": "장소명을 인식할 수 없거나, 해당 지역에 추천할 만한 식당이 없습니다. 더 자세한 장소명으로 다시 질문해주세요."}]
            }

        return {
            "location": location,
            "menu": menu,
            "context": context,
            "user_input": user_input # 다음 노드들을 위해 user_input 전달
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
    return {"candidates": candidates, "user_input": state["user_input"]}

async def detail_node(state: State) -> dict:
    details = get_restaurant_info(state["candidates"])
    return {"restaurant_details": details, "user_input": state["user_input"]}

async def final_node(state: State) -> dict:  
    result_list = await final_recommend(state["restaurant_details"], state["user_input"])
    return {"result": result_list}

def next_tool_selector(state: dict) -> str:
    if state.get("end") is True:
        return "__end__"
    return "intersection_node"

graph_builder = StateGraph(State)

graph_builder.add_node("extract_filters", RunnableLambda(extract_all))
graph_builder.add_node("intersection_node", intersection_node)
graph_builder.add_node("detail_node", detail_node)
graph_builder.add_node("final_node", final_node)

graph_builder.set_entry_point("extract_filters")

graph_builder.add_conditional_edges(
    "extract_filters",
    next_tool_selector,
    {
        "intersection_node": "intersection_node",
        "__end__": END
    }
)
graph_builder.add_edge("intersection_node", "detail_node")
graph_builder.add_edge("detail_node", "final_node")
graph_builder.add_edge("final_node", END)

async def run_recommendation_pipeline(state: dict) -> dict:
    graph = graph_builder.compile()
    result = await graph.ainvoke(state)
    return result
