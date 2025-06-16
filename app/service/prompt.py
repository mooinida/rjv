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
아래는 여러 식당에 대한 AI 분석 결과입니다.

[사용자 요청]
{user_input}

[AI 분석 결과]
{analyzed_results}
                                                            

조건:
- 사용자의 요청에 어울리는 식당을 5곳 추천해주세요.
- 어울린다고 생각한 이유도 설명해주세요.
아래 형식으로 정리해서 답해주세요:

1. 식당 이름 - 상세점보:식당url
2. 추천이유                                     
3. AI평점 , 실제평점
""")

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
