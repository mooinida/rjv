from langchain_core.prompts import PromptTemplate

# --- 리뷰 분석용 프롬프트 ---
review_prompt_template = PromptTemplate.from_template("""
식당 이름 (정확한 상호명): {name}
실제 평점: {rating}
리뷰 수: {reviewCount}
식당 URL: {url}
아래는 이 식당의 리뷰입니다:
------------------------------
{review_text}
------------------------------

다음 형식에 따라 응답하세요:
1. 식당 이름 (상호명) - 상세정보: 식당 url
2. 추천 이유 (리뷰 키워드 기반)
3. AI 예상 평점 / 실제 평점
""")

# --- 최종 추천을 위한 프롬프트 (JSON 출력 요청) ---
final_selection_prompt_template = PromptTemplate.from_template("""
당신은 음식점 추천 AI 큐레이터입니다.
다음은 개별 식당에 대한 리뷰 분석 결과입니다. 각 결과에는 식당의 실제 이름과 URL이 포함되어 있습니다.

이 분석 결과를 기반으로, **정확한 식당 상호명**을 사용하여 가장 추천하고 싶은 음식점 5곳을 JSON 배열로 추출해주세요.

[사용자 요청]: {user_input}

[AI 분석 결과]:
{analyzed_results}

[출력 형식]:
- 반드시 JSON 배열로 응답하세요.
- JSON 배열의 각 요소는 아래와 같은 키를 가져야 합니다:
  - name: 실제 식당 상호명 (예: '스시히로바')
  - reason: 추천 이유 (간결하고 명확하게)
  - aiRating: AI가 분석한 예상 만족도 (예: 4.8)
  - actualRating: 실제 평점 (예: 4.3)
- 예시:
[
  {
    "name": "스시히로바",
    "reason": "리뷰에서 신선한 재료와 조용한 분위기가 반복적으로 언급됨",
    "aiRating": 4.8,
    "actualRating": 4.3
  },
  ...
]
- 다른 설명이나 마크다운, ```json 등의 태그는 절대 포함하지 마세요.
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
