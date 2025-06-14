# service/prompt.py

from langchain_core.prompts import PromptTemplate

# [필수] 개별 식당 분석에 사용되는 프롬프트입니다.
review_prompt_template = PromptTemplate.from_template("""
아래 식당 정보를 보고 추천 이유를 분석하고, JSON 형식으로 출력해주세요.

식당 이름: {name}
실제 평점: {rating}
리뷰 수: {reviewCount}
식당 url: {url}

리뷰들:
{review_text}

아래 JSON 형식을 따르세요:
{{
  "name": "{name}",
  "url": "{url}",
  "reason": "...추천 이유...",
  "aiRating": 4.3,
  "realRating": {rating}
}}
""")

# [수정 완료된] 최종 추천 결과 생성을 위한 프롬프트입니다.
final_selection_prompt_template = PromptTemplate.from_template("""
You are a helpful AI assistant that provides restaurant recommendations in a structured JSON format.
Based on the user's request and the provided analysis for several restaurants, generate a JSON array of up to 5 recommended restaurants.

[User Request]
{user_input}

[Analyzed Restaurant Details]
{analyzed_results}

RULES:
- The output MUST be a valid JSON array. Each object in the array represents one restaurant.
- Each JSON object must contain the following keys: "placeId", "name", "description", "aiRating", "actualRating", "url".
- The "description" should be a friendly and comprehensive paragraph explaining why the restaurant is a good match, based on the analysis.
- The "aiRating" and "actualRating" should be string values (e.g., "4.5").
- Do not include any text, explanations, or markdown formatting outside of the final JSON array.
""")

# [필수] 컨텍스트 분석에 사용되는 프롬프트입니다.
context_prompt_template= PromptTemplate.from_template("""
    식당 이름: {name}
    실제 평점: {rating}
    리뷰 수: {reviewCount}

    아래는 이 식당에 대한 실제 리뷰입니다:
    ------------------------------
    {review_text}
    ------------------------------

    리뷰를 기반으로 이 식당이 다음과 같은 측면에서 어떤지 판단하세요:
    - 상황 (예: 혼밥, 회식, 가족 외식 등)
    - 분위기 (예: 조용한, 감성적인, 활기찬 등)
    - 목적 (예: 데이트, 가볍게 한잔 등)

    이 식당을 특정 상황/분위기/목적으로 추천할 수 있는 이유를 설명하고, AI 별점을 부여하세요.

    형식:
    식당 이름) - 상세점보):식당url
    추천이유)                                     
    AI평점) , 실제평점)
    """)

# ★★★ [오류 원인] 이 함수가 누락되었을 가능성이 높습니다. ★★★
def build_review_prompt(restaurant: dict) -> str:
    reviews = restaurant.get("reviews", [])
    review_text = "\\n".join([rev["text"] for rev in reviews])
    return review_prompt_template.format(
        name=restaurant.get("name", "이름 없음"),
        rating=restaurant.get("rating", 0.0),
        reviewCount=restaurant.get("reviewCount", 0),
        url=restaurant.get("url", "URL 없음"),
        review_text=review_text
    )

# [수정 완료된] 최종 추천 프롬프트 빌더입니다.
def build_final_recommendation_prompt(analyzed_restaurants: dict, input_text: str) -> str:
    text_blocks = []
    restaurant_list = analyzed_restaurants.get("restaurants", [])
    for r in restaurant_list:
        review_texts = "\\n".join([rev.get("text", "") for rev in r.get("reviews", [])])
        block = (
            f"placeId: {r.get('placeId')}\\n"
            f"name: {r.get('name')}\\n"
            f"url: {r.get('url')}\\n"
            f"actualRating: {r.get('rating')}\\n"
            f"reviewCount: {r.get('reviewCount')}\\n"
            f"reviews: {review_texts[:500]}..."
        )
        text_blocks.append(block)

    combined_analysis = "\\n\\n---\\n\\n".join(text_blocks)

    return final_selection_prompt_template.format(
        user_input=input_text,
        analyzed_results=combined_analysis
    )

# [필수] 컨텍스트 프롬프트 빌더입니다.
def build_context_prompt(restaurant:dict):
    reviews = restaurant.get("reviews", [])
    review_text = "\\n".join([rev["text"] for rev in reviews])
    return context_prompt_template.format(
    name=restaurant.get("name", "이름 없음"),
    rating=restaurant.get("rating", 0.0),
    reviewCount=restaurant.get("reviewCount", 0),
    url=restaurant.get("url", "URL 없음"),
    review_text=review_text
    )
