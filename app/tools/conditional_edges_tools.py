from langchain_core.tools import tool
@tool
def restart(input_text: str):
    """음식추천을 다시 시작하는 함수입니다."""
    return {
        "status": "done",
        "action": "restart",
        "message": "✅ 추천을 처음부터 다시 시작합니다. LangGraph에서 재추천을 처리합니다."
    }


@tool
def show_menu(input_text: str):
    """해당 식당의 메뉴를 보여주는 함수입니다. 사용자의 질문과 해당되는 도구라고 생각하면 해당 도구를 선택하고 다시 호출하지 않습니다."""
    return (
    "요약: 사용자가 새로운 추천을 원함\n"
    "결과: 추천을 처음부터 다시 시작합니다. LangGraph에서 재추천을 처리합니다.\n"
    "✅ 작업 완료"
)


@tool
def another_restaurants(input_text: str):
    """다른 식당의 정보를 구하는 함수입니다. 사용자의 질문과 해당되는 도구라고 생각하면 해당 도구를 선택하고 다시 호출하지 않습니다."""
    return (
    "요약: 사용자가 새로운 추천을 원함\n"
    "결과: 추천을 처음부터 다시 시작합니다. LangGraph에서 재추천을 처리합니다.\n"
    "✅ 작업 완료"
)

@tool
def another_menu(input_text: str):
    """다른 메뉴를 찾을 때 쓰는 함수입니다. 사용자의 질문과 해당되는 도구라고 생각하면 해당 도구를 선택하고 다시 호출하지 않습니다."""
    return (
    "요약: 사용자가 새로운 추천을 원함\n"
    "결과: 추천을 처음부터 다시 시작합니다. LangGraph에서 재추천을 처리합니다.\n"
    "✅ 작업 완료"
)

    