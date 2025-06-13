from service.prompt import build_review_prompt, build_final_recommendation_prompt
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
import asyncio
import json # ⬅️ JSON 파싱을 위해 추가
import re   # ⬅️ 정규식으로 JSON만 깔끔하게 추출하기 위해 추가

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# 스트리밍을 사용하지 않는 것이 최종 JSON 결과물을 얻기에 더 안정적일 수 있습니다.
llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-pro", google_api_key=GOOGLE_API_KEY)

async def call_llm(prompt: str, print_result: bool):
    # 스트리밍을 사용하지 않고 전체 결과를 한 번에 받도록 수정
    result = await llm.ainvoke(prompt)
    if print_result:
        print(result.content)
    return result.content

async def analyze_restaurant(restaurant: dict) -> dict:
    prompt = build_review_prompt(restaurant)
    response_content = await call_llm(prompt, print_result=False)
    result = {
        "placeId": restaurant["placeId"],
        "name": restaurant["name"],
        "url": restaurant["url"],
        "llmResult": response_content # .content를 사용
    }
    return result

async def run_llm_analysis(data: dict) -> list:
    restaurants = data.get("restaurants", [])
    if not isinstance(restaurants, list):
        raise ValueError("restaurants는 리스트여야 합니다.")

    tasks = [analyze_restaurant(r) for r in restaurants]
    return await asyncio.gather(*tasks)


# ✅✅✅ 이 함수가 핵심적인 수정 부분입니다. ✅✅✅
async def get_final_recommendation(results: list, input_text:str) -> list:
    """
    AI가 생성한 JSON 형식의 문자열 응답을 파싱하여 파이썬 리스트로 반환합니다.
    """
    # service/prompt.py에서 수정한, JSON을 요청하는 프롬프트를 생성합니다.
    final_prompt = build_final_recommendation_prompt(results, input_text)
    response_text = await call_llm(final_prompt, print_result=False)
    print("AI 원본 응답 (JSON):", response_text) # 디버깅용 로그

    try:
        # AI가 응답 앞뒤에 추가적인 텍스트(예: "추천 결과입니다.")나 ```json 마크다운을 붙이는 경우에 대비해
        # 정규식으로 순수한 JSON 부분만 추출합니다.
        json_match = re.search(r"\[[\s\S]*\]", response_text)
        if not json_match:
            raise json.JSONDecodeError("응답에서 JSON 배열을 찾을 수 없습니다.", response_text, 0)
        
        json_str = json_match.group(0)
        
        # 추출한 JSON 문자열을 파이썬 리스트 객체로 변환합니다.
        parsed_json = json.loads(json_str)
        return parsed_json

    except json.JSONDecodeError as e:
        print(f"❌ 최종 추천 결과 JSON 파싱 실패: {e}")
        # 파싱 실패 시, 프론트엔드에서 에러를 인지할 수 있도록 에러 메시지를 담은 리스트를 반환합니다.
        return [{"error": "AI 답변 형식 오류로 결과를 표시할 수 없습니다."}]
