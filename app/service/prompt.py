from langchain_core.prompts import PromptTemplate

# review_prompt_template, context_prompt_template은 그대로 유지

# 최종 결과물의 형식을 결정하는 final_selection_prompt_template을 수정합니다.
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
- The "description" should be a friendly and comprehensive paragraph explaining why the restaurant is a good match, based on the analysis from reviews.
- The "aiRating" and "actualRating" should be string values (e.g., "4.5").
- Do not include any text, explanations, or markdown formatting outside of the final JSON array.
""")

# 최종 프롬프트에 데이터를 삽입하는 함수를 수정합니다.
def build_final_recommendation_prompt(analyzed_restaurants: list, input_text: str) -> str:
    text_blocks = []
    # 'restaurants' 키가 있는지 확인하고 리스트를 가져옵니다.
    restaurant_list = analyzed_restaurants.get("restaurants", [])
    for r in restaurant_list:
        # 개별 식당의 정보를 텍스트 블록으로 만들어 LLM에게 참고자료로 전달
        review_texts = "\\n".join([rev.get("text", "") for rev in r.get("reviews", [])])
        block = (
            f"placeId: {r.get('placeId')}\\n"
            f"name: {r.get('name')}\\n"
            f"url: {r.get('url')}\\n"
            f"actualRating: {r.get('rating')}\\n"
            f"reviewCount: {r.get('reviewCount')}\\n"
            f"reviews: {review_texts[:500]}..."  # 리뷰가 너무 길 경우를 대비해 일부만 사용
        )
        text_blocks.append(block)

    combined_analysis = "\\n\\n---\\n\\n".join(text_blocks)

    return final_selection_prompt_template.format(
        user_input=input_text,
        analyzed_results=combined_analysis
    )

# build_review_prompt, build_context_prompt는 그대로 유지
