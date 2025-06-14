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
당신은 음식점 추천 AI 큐레이터입니다.
사용자 요청과 AI 분석 결과를 바탕으로, 가장 적합한 음식점 5개를 JSON 배열 형식으로 추천해주세요.
[사용자 요청]: {user_input}
[AI 분석 결과]:
{analyzed_results}
[출력 형식]:
- 반드시 JSON 배열 형식으로만 응답해야 합니다.
- 다른 부가적인 설명이나 인사는 절대 포함하지 마세요.
- JSON 배열의 각 요소는 name, reason, aiRating, actualRating 키를 가진 객체여야 합니다.
- 예시: [ {{"name": "...", "reason": "...", "aiRating": "...", "actualRating": "..."}}, ... ]
""")


# --- 프롬프트 생성 헬퍼 함수들 ---

def build_review_prompt(restaurant: dict) -> str:
    reviews = restaurant.get("reviews", [])
    review_text = "\n".join([rev["text"] for rev in reviews])
