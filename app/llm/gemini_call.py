from service.prompt import build_review_prompt, build_final_recommendation_prompt
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
import asyncio
import json
import re

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-pro", google_api_key=GOOGLE_API_KEY)

async def call_llm(prompt: str, print_result: bool = False) -> str:
    result = await llm.ainvoke(prompt)
    if print_result:
        print("🔍 LLM 응답:", result.content)
    return result.content

async def analyze_restaurant(restaurant: dict) -> dict:
    prompt = build_review_prompt(restaurant)
    response = await call_llm(prompt)
    return {
        "placeId": restaurant["placeId"],
        "name": restaurant["name"],
        "url": restaurant["url"],
        "llmResult": response
    }

async def run_llm_analysis(data: dict) -> list:
    restaurants = data.get("restaurants", [])
    if not isinstance(restaurants, list):
        raise ValueError("'restaurants' 필드는 리스트여야 합니다.")
    return await asyncio.gather(*(analyze_restaurant(r) for r in restaurants))

async def get_final_recommendation(results: list, input_text: str) -> list:
    """
    AI가 생성한 JSON 형식의 문자열 응답을 파싱하여 파이썬 리스트로 반환합니다.
    """

    final_prompt = build_final_recommendation_prompt(results, input_text)

    # ✅ 여기에서 응답을 출력하도록 수정 (True로 변경)
    response_text = await call_llm(final_prompt, print_result=True)  # ✅ 로그 출력

    print("🎯 Gemini LLM 응답 원문 ↓↓↓")
    print(response_text)  # ✅ 반드시 찍히도록 이 줄도 추가!

    try:
        json_match = re.search(r"\[[\s\S]*\]", response_text)
        if not json_match:
            print("❌ JSON 정규식 매칭 실패. 전체 응답:\n", response_text)
            raise ValueError("LLM 응답에서 JSON 배열을 찾을 수 없습니다.")
        
        json_str = json_match.group(0)
        parsed_json = json.loads(json_str)
        return parsed_json

    except json.JSONDecodeError as e:
        print(f"❌ 최종 추천 결과 JSON 파싱 실패: {e}")
        return [{"error": "AI 답변 형식 오류로 결과를 표시할 수 없습니다."}]
