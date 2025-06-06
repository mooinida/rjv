import os
import sys
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langgraph.graph import StateGraph, END
from langchain_core.runnables import Runnable
from typing import TypedDict
from langchain_core.runnables import RunnableLambda
from agent.conditional_edges import route_by_agent
from tools.gpt_tools import (
    get_location_tool,
    get_menu_tool,
    get_context_tool,
    intersection_restaurant,
    get_restaurant_info,
    final_recommend,
)
from service.saveRestaurant_pipeline import next_tool

# ✅ 수정: 상태에 user_input 포함
class State(TypedDict):
    user_input: str
    location: list
    menu: list
    context: list
    candidates: dict          
    restaurant_details: dict  
    result: dict

# ✅ 각 노드에서 user_input을 다음 상태로 명시적으로 넘겨줘야 함
async def location_node(state: State) -> dict:
    location = await get_location_tool(state["user_input"])
    return {
        "location": location,
        "user_input": state["user_input"]  # ← 추가
    }

async def menu_node(state: State) -> dict:
    menu = await get_menu_tool(state["user_input"])
    return {
        "menu": menu,
        "user_input": state["user_input"]  # ← 추가
    }

async def context_node(state: State) -> dict:
    context = await get_context_tool(state["user_input"])
    return {
        "context": context,
        "user_input": state["user_input"]  # ← 추가
    }

async def intersection_node(state: State) -> dict:
    candidates = intersection_restaurant(
        state["location"],
        state["menu"],
        state["context"]
    )
    return {"candidates": candidates}


async def detail_node(state: State) -> dict:
    details = get_restaurant_info(state["candidates"])
    return {"restaurant_details": details}  # ✅ 키 이름 변경

async def final_node(state: State) -> dict:
    result = await final_recommend(state["restaurant_details"], state["user_input"])
    print("📦 final_node result:", result)
    return {"result": result}  # ✅ 키 이름 변경


# LangGraph 설정
graph_builder = StateGraph(State)

graph_builder.add_node("location_node", location_node)
graph_builder.add_node("menu_node", menu_node)
graph_builder.add_node("context_node", context_node)
graph_builder.add_node("intersection_node", intersection_node)
graph_builder.add_node("detail_node", detail_node)
graph_builder.add_node("final_node", final_node)
graph_builder.add_node("branch_node", RunnableLambda(lambda x: x))

# 흐름 연결도 이름에 맞게 수정
graph_builder.set_entry_point("location_node")
graph_builder.add_edge("location_node", "menu_node")
graph_builder.add_edge("menu_node", "context_node")
graph_builder.add_edge("context_node", "intersection_node")
graph_builder.add_edge("intersection_node", "detail_node")
graph_builder.add_edge("detail_node", "final_node")
graph_builder.add_edge("final_node", END)


# 실행 함수
async def run_recommendation_pipeline(state: dict) -> dict:
    graph = graph_builder.compile()
    result = await graph.ainvoke(state)
    print(result)
    return result

async def run_from_node(state: dict, entry_node: str) -> dict:
    # graph_builder는 이미 LangGraph 정의됨
    graph = graph_builder.compile()

    # ✅ entry_point를 동적으로 바꿔서 실행
    partial_graph = graph.with_config({"entry_point": entry_node})
    result = await partial_graph.ainvoke(state)

    return result
# 테스트
async def main():
    state = {"user_input": input("처음 요청을 입력하세요: ")}

    while True:
        if "result" not in state:
            # 최초 실행 또는 restart 요청 시 전체 파이프라인 실행
            state = await run_recommendation_pipeline(state)
            print("\n📍 추천 결과:")
            print(state.get("result"))
        else:
            # 추천 이후 분기된 요청 처리
            followup = input("\n👉 추가 요청을 입력하세요 (종료하려면 exit): ")
            if followup.lower() == "exit":
                break

            state["user_input"] = followup
            next_node = next_tool(state)
            if next_node == "end":
                break

            # ✅ 이전 결과를 삭제 (다시 추천하도록 유도)
            state.pop("result", None)

            state = await run_from_node(state, entry_node=next_node)




if __name__ == "__main__":
    asyncio.run(main())
