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

# --- 토큰 관리 관련 import (자동 갱신 관련 제거) ---
# bring_to_server의 refresh_access_token_if_needed 등은 이제 직접 호출하지 않음
# get_menu, review_fetch의 httpx 갱신 함수도 제거 (각 _make_authenticated_request_httpx 내에서만 사용)


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
        "user_input": state["user_input"]
    }

async def menu_node(state: State) -> dict:
    menu = await get_menu_tool(state["user_input"])
    return {
        "menu": menu,
        "user_input": state["user_input"]
    }

async def context_node(state: State) -> dict:
    context = await get_context_tool(state["user_input"])
    return {
        "context": context,
        "user_input": state["user_input"]
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
    return {"restaurant_details": details}

async def final_node(state: State) -> dict:
    result = await final_recommend(
        state["user_id"],              # ← user_id 따로 넘기기
        state["restaurant_details"],  # ← 이건 dict임
        state["user_input"]
    )
    return {
        "result": result["result"],
        "restaurant_aiRating": result["aiRating"]
    }


# LangGraph 설정
graph_builder = StateGraph(State)

graph_builder.add_node("location_node", location_node)
graph_builder.add_node("menu_node", menu_node)
graph_builder.add_node("context_node", context_node)
graph_builder.add_node("intersection_node", intersection_node)
graph_builder.add_node("detail_node", detail_node)
graph_builder.add_node("final_node", final_node)


graph_builder.set_entry_point("location_node")
graph_builder.add_edge("location_node", "menu_node")
graph_builder.add_edge("menu_node", "context_node")
graph_builder.add_edge("context_node", "intersection_node")
graph_builder.add_edge("intersection_node", "detail_node")
graph_builder.add_edge("detail_node", "final_node")
graph_builder.add_edge("final_node", END)


# 실행 함수 (인증 오류 처리 간소화)
async def run_recommendation_pipeline(state: dict) -> dict:
    graph = graph_builder.compile()
    try:
        result = await graph.ainvoke(state)
        print(result)
        return result
    except RuntimeError as e: # 인증 실패 예외는 여기에서 처리 (상위 호출자에게 전달)
        print(f"\n❌ 애플리케이션 실행 실패: {e}")
        # 오류 메시지를 사용자에게 안내하고, 재로그인을 유도
        return {"error": f"Authentication required: {e}. Please log in manually."}


async def run_from_node(state: dict, entry_node: str) -> dict:
    graph = graph_builder.compile()
    try:
        partial_graph = graph.with_config({"entry_point": entry_node})
        result = await partial_graph.ainvoke(state)
        return result
    except RuntimeError as e:
        print(f"\n❌ 애플리케이션 실행 실패: {e}")
        return {"error": f"Authentication required: {e}. Please log in manually."}


# 테스트 (자동 토큰 관리 로직 제거)
async def main():
    # 초기 토큰 유효성 검사 및 갱신 로직 제거
    # JWT_TOKEN은 이제 FastAPI 미들웨어에서 받아서 os.environ에 설정될 것으로 기대
    # 즉, 이 스크립트 실행 전에는 JWT_TOKEN이 os.environ에 없어도 됩니다.

    state = {"user_input": input("처음 요청을 입력하세요: ")}

    while True:
        if "result" not in state or ("error" in state and "Authentication required" in state["error"]):
            state = await run_recommendation_pipeline(state)
            if "error" in state: 
                print("\n🚫 LangGraph 실행 중 인증 오류 발생. 프론트엔드에서 다시 로그인해주세요.")
                break # 프로그램 종료
            print("\n📍 추천 결과:")
            print(state.get("result"))
        else:
            followup = input("\n👉 추가 요청을 입력하세요 (종료하려면 exit): ")
            if followup.lower() == "exit":
                break

            state["user_input"] = followup
            next_node = next_tool(state)
            if next_node == "end":
                break

            state.pop("result", None)
            state = await run_from_node(state, entry_node=next_node)


if __name__ == "__main__":
    asyncio.run(main())
