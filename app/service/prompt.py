from langchain_core.prompts import PromptTemplate

review_prompt_template = PromptTemplate.from_template("""
식당 이름: {name}
실제 평점: {rating}
리뷰 수: {reviewCount}
식당 url:{url}
아래는 이 식당의 리뷰입니다:
------------------------------
{review_text}
------------------------------

1. 식당 이름 - 상세점보:식당url
2. 추천이유                                     
3. AI평점 , 실제평점
""")

final_selection_prompt_template = PromptTemplate.from_template("""
당신은 사용자의 요청에 가장 적합한 음식점 5개를 분석 결과를 바탕으로 추천하는 AI 큐레이터입니다.

[사용자 요청]
{user_input}

[AI 분석 결과]
{analyzed_results}

위 분석 결과를 바탕으로, 사용자의 요청에 가장 부합하는 음식점 5개를 골라 아래의 JSON 형식에 맞춰서 추천해주세요.
- 각 필드는 쌍따옴표로 감싸야 합니다.
- 추천 이유는 1~2 문장으로 간결하게 작성해주세요.
- 다른 설명 없이 JSON 데이터만 응답해야 합니다.

```json
[
  {{
    "name": "식당 이름",
    "reason": "추천 이유",
    "aiRating": "AI 평점(예: 4.8)",
    "actualRating": "실제 평점(예: 4.5)"
  }},
  {{
    "name": "두 번째 식당 이름",
    "reason": "두 번째 식당 추천 이유",
    "aiRating": "4.7",
    "actualRating": "4.9"
  }}
]

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

def build_final_recommendation_prompt(analyzed_restaurants: list, input_text:str) -> str:
    text_blocks = []
    for r in analyzed_restaurants:
        name = r["name"]
        url = r["url"]
        content = (
            r["llmResult"].content if hasattr(r["llmResult"], "content") else str(r["llmResult"])
        )
        text_blocks.append(f" {name}\n URL: {url}\n{content.strip()}")

    combined = "\n\n".join(text_blocks)

    return final_selection_prompt_template.format_prompt(
        user_input = input_text,
        analyzed_results=combined
    ).to_string()


def build_context_prompt(restaurant:dict):
    reviews = restaurant.get("reviews", [])
    review_text = "\n".join([rev["text"] for rev in reviews])
    return context_prompt_template.format(
    name=restaurant.get("name", "이름 없음"),
    rating=restaurant.get("rating", 0.0),
    reviewCount=restaurant.get("reviewCount", 0),
    url=restaurant.get("url", "URL 없음"),
    review_text=review_text
    )
