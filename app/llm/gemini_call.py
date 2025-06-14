# llm/gemini_call.py

from service.prompt import build_review_prompt, build_final_recommendation_prompt
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
import asyncio
import json # JSON 파싱을 위해 import
import re   # 정규표현식을 이용해 LLM 응답에서 JSON만 추출하기 위해 import

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="models/gemini-1.5-pro",
    google_api_key=GOOGLE_API_KEY,
    # 스트리밍을 사용하면 첫 응답까지의 시간을 줄일 수 있습니다.
    model_kwargs={"streaming": True} 
)

async def call_llm(prompt: str, print_result: bool = False):
    """LLM을 호출하고 스트리밍된 응답을 받아 하나의 문자열로 합칩니다."""
    stream = llm.astream(prompt)
    result = ""
    async for chunk in stream:
        if chunk.content:
            result += chunk.content
    
    if print_result:
        print("LLM Final Response:\n", result)
        
    return result

async def analyze_restaurant(restaurant: dict) -> dict:
    """개별 식당의 정보를 받아 LLM으로 추천 이유 등을 분석합니다."""
    prompt = build_review_prompt(restaurant)
    # 개별 분석 결과는 디버깅 목적 외에는 출력할 필요가 없으므로 print_result=False
    response = await call_llm(prompt, print_result=False) 
    
    result = {
        "placeId": restaurant["placeId"],
        "name": restaurant["name"],
        "url": restaurant["url"],
        "llmResult": response # 분석 결과 저장
    }
    return result

async def run_llm_analysis(data: dict) -> list:
    """여러 식당을 병렬로 분석합니다."""
    restaurants = data.get("restaurants", [])
    if not isinstance(restaurants, list):
        raise ValueError("restaurants는 리스트여야 합니다.")

    tasks = [analyze_restaurant(r) for r in restaurants]
    return await asyncio.gather(*tasks)


# ★★★ 핵심 수정 부분 ★★★
async def get_final_recommendation(results: dict, input_text: str) -> list:
    """
    개별 분석 결과를 종합하고, 최종 프롬프트를 생성하여 LLM에게 JSON 응답을 요청합니다.
    LLM의 응답(문자열)을 파싱하여 JSON 객체 리스트로 변환하여 반환합니다.
    """
    final_prompt = build_final_recommendation_prompt(results, input_text)
    llm_response_str = await call_llm(final_prompt, print_result=True)

    try:
        # LLM이 응답 앞뒤에 추가적인 텍스트(예: "물론이죠. 추천 결과입니다:")를 붙이는 경우가 있으므로,
        # 정규표현식을 사용해 JSON 배열 부분만 정확히 추출합니다.
        json_match = re.search(r'\[.*\]', llm_response_str, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            # 추출된 JSON 문자열을 파이썬 리스트 객체로 변환합니다.
            return json.loads(json_str)
        else:
            print("⚠️ LLM 응답에서 JSON 배열을 찾지 못했습니다.")
            # 프론트엔드에서 에러를 표시할 수 있도록 에러 메시지를 담은 객체를 리스트에 넣어 반환합니다.
            return [{"error": "추천을 생성하는 데 실패했습니다. 응답 형식이 올바르지 않습니다."}]
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 실패: {e}")
        return [{"error": f"추천을 생성하는 데 실패했습니다: {e}"}]
