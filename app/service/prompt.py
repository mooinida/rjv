from langchain_core.prompts import PromptTemplate

# --- 리뷰 분석용 프롬프트 ---
review_prompt_template = PromptTemplate.from_template("""
식당 이름: {name}
실제 평점: {rating}
리뷰 수: {reviewCount}
식당 url: {url}
아래는 이 식당의 리뷰입니다:
------------------------------
{review_text}
------------------------------

1. 식당 이름 - 상세정보: 식당 url
2. 추천이유
3. AI평점 , 실제평점
""")

# --- 최종 추천을 위한 프롬프트 (JSON 출력 요청) ---
# ✅✅✅ 문법 오류를 원천적으로 차단하기 위해 프롬프트 구조를 변경했습니다. ✅✅✅
final_selection_prompt_template = PromptTemplate.from_template("""
당신은 사용자의 요청과 각 식당의 분석 내용을 바탕으로, 각 식당이 얼마나 적합한지 0.0에서 5.0 사이의 점수로만 평가하는 평가자입니다.

[사용자 요청]: {user_input}

[AI 분석 결과]:
{analyzed_results}

[지시사항]:
- 위 [AI 분석 결과]에 있는 각 식당의 이름과 분석 내용을 보고, [사용자 요청]에 얼마나 부합하는지 점수를 매겨주세요.
- 다른 설명은 일절 하지 말고, 아래와 같은 JSON 형식으로만 응답해야 합니다.
- 각 식당의 이름은 key가 되고, 당신이 매긴 점수는 value가 되어야 합니다.

{{
  "식당 이름 1": "5.0",
  "식당 이름 2": "4.7",
  "식당 이름 3": "4.5"
}}
""")

# --- 프롬프트 생성 헬퍼 함수들 ---

def build_review_prompt(restaurant: dict) -> str:
    reviews = restaurant.get("reviews", [])
    review_text = "\n".join([rev["text"] for rev in reviews])
    return review_prompt_template.format_prompt(
        name=restaurant.get("name", "이름 없음"),
        rating=restaurant.get("rating", 0.0),
        reviewCount=restaurant.get("reviewCount", 0),
        url=restaurant.get("url", "URL 없음"),
        review_text=review_text
    ).to_string()

def build_final_recommendation_prompt(analyzed_restaurants: list, input_text: str) -> str:
    text_blocks = []
    for r in analyzed_restaurants:
        name = r.get("name", "이름 없음")
        url = r.get("url", "URL 없음")
        content = r.get("llmResult", "")
        text_blocks.append(f"== 식당 정보 ==\n이름: {name}\nURL: {url}\n분석 내용: {str(content).strip()}")

    combined = "\n\n".join(text_blocks)

    return final_selection_prompt_template.format(
        user_input=input_text,
        analyzed_results=combined
    )
