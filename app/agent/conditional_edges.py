from agent.agent_config import agent  # agent 불러오기

def route_by_agent(state: dict) -> str:
    followup = state.get("user_input", "")   

    # 👇 프롬프트를 넣어서 agent 호출
    result = agent.invoke({"input": prompt})
    print("🧾 Agent 결과 전체:", result)

    steps = result.get("intermediate_steps", [])
    tool_name = None

    if steps:
        try:
            tool_name = steps[-1][0].tool  # 마지막 도구 호출 이름
        except Exception as e:
            print(f"⚠️ 도구 추출 실패: {e}")

    if not tool_name:
        print("❌ 도구 판단 실패. 종료로 분기")
        return "end"

    print(f"🔀 분기 판단: {tool_name}")

    return {
        "restart": "location_node",
        "show_menu": "menu_node",
        "another_restaurants": "intersection_node",
        "another_menu": "menu_node",
    }.get(tool_name, "end")
