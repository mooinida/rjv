from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from langgraph.graph.message import add_messages
from typing import Annotated, TypedDict

from tools.gpt_tools import (
    get_location_tool,
    get_menu_tool,
    get_context_tool,
    intersection_restaurant,
    get_restaurant_info,
    final_recommend,
)

class GraphState(TypedDict):
    user_input: str
    location: list
    menu: list
    context: list
    intersection: dict
    restaurant_info: dict
    result: dict

builder = StateGraph(GraphState)

# 1. 위치
builder.add_node("location", RunnableLambda(lambda x: get_location_tool(x["user_input"])))
builder.set_entry_point("location")

# 2. 메뉴
builder.add_node("menu", RunnableLambda(lambda x: get_menu_tool(x["user_input"])))

# 3. 분위기/상황
builder.add_node("context", RunnableLambda(lambda x: get_context_tool(x["user_input"])))

# 4. 교집합 필터링
builder.add_node("intersection", RunnableLambda(lambda x: intersection_restaurant(x["location"], x["menu"], x["context"])))

# 5. 식당 상세 정보
builder.add_node("restaurant_info", RunnableLambda(lambda x: get_restaurant_info(x["intersection"])))

# 6. LLM 기반 최종 추천
builder.add_node("final_recommend", RunnableLambda(lambda x: final_recommend(x["restaurant_info"])))

# 메시지 통합용 (선택 사항)
builder.add_edge("location", "menu")
builder.add_edge("menu", "context")
builder.add_edge("context", "intersection")
builder.add_edge("intersection", "restaurant_info")
builder.add_edge("restaurant_info", "final_recommend")
builder.set_finish_point("final_recommend")

graph = builder.compile()