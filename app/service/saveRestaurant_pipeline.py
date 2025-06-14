# app/service/saveRestaurant_pipeline.py

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
import json
import re
import os
import math
from dotenv import load_dotenv
import aiohttp

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-pro", google_api_key=GOOGLE_API_KEY)

async def get_location_and_context(text: str):
    prompt = PromptTemplate.from_template(
    """다음 문장에서 식당을 고를 때 고려하는 분위기, 목적, 상황, 선호도 등을 모두 추출해줘.
        음식 종류나 장소 이름은 빼고, 
        분위기, 환경, 사용자 의도(예: 혼밥, 데이트, 가성비, 회식, 분위기좋은 등)를 중심으로 짧은 단위로 나눠서 정리해줘.
        해당하는 게 없다면 빈 리스트를 반환해.
        ------------------------------
        문장: {text}
        ------------------------------
        답변형식: {{"keywords": ["혼밥", "조용한", "가볍게 한잔"]}}
        """
    )
    chain = prompt | llm
    result = await chain.ainvoke({"text": text})
    try:
        json_str = re.search(r'\{.*\}', result.content, re.DOTALL)
        if json_str:
            data = json.loads(json_str.group())
            return data.get("keywords", [])
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 실패: {e}")
    return []

async def get_location_and_menu(text: str):
    prompt = PromptTemplate.from_template("""다음 문장에서 사용자가 원하는 음식 키워드 또는 카테고리를 추출해줘.
        최대한 짧은 단위로 나눠. 쓸모없는 키워드는 제거. 메뉴에 대해 없다면 빈 리스트 반환해.
        ex)매운 음식-> 매운, 초밥집->초밥, 고깃집->고기, 카페->카페,아메리카노
        ------------------------------
        문장: {text}
        ------------------------------
        답변형식: {{"keywords": ["짜장면", "짬뽕", "중식"]}}
        """
    )
    chain = prompt | llm
    result = await chain.ainvoke({"text": text})
    try:
        json_str = re.search(r'\{.*\}', result.content, re.DOTALL)
        if json_str:
            data = json.loads(json_str.group())
            return data.get("keywords", [])
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 실패: {e}")
    return []

async def get_location_from_text(text: str) -> str:
    prompt = PromptTemplate.from_template("다음 문장에서 장소명(예: 지역, 건물, 역 등)만 정확히 추출해줘. 설명하지 말고 장소명만 말해. 장소,지역명이 없으면 빈 리스트 리턴하시오. 문장: {text}")
    chain = prompt | llm
    result = await chain.ainvoke({"text": text})
    return result.content.strip()

async def get_coordinates_from_location(location: str):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": location, "key": GOOGLE_API_KEY}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                if data.get("status") == "OK" and data.get("results"):
                    loc = data["results"][0].get("geometry", {}).get("location", {})
                    return {"latitude": loc.get("lat"), "longitude": loc.get("lng")}
                else:
                    return {"error": f"API 실패: {data.get('status')}, {data.get('error_message', '원인 미상')}"}
    except Exception as e:
        return {"error": f"예외 발생: {str(e)}"}    

def filtering_restaurant(restaurants: dict) -> list[int]:
    """
    평점과 리뷰 수를 기반으로 식당의 점수를 매기고,
    상위 10개 식당의 placeId 리스트를 반환합니다.
    """
    filtered_restaurants = []
    
    for r in restaurants.get("restaurants", []):
        try:
            if int(r.get("reviewCount", 0)) >= 1:
                filtered_restaurants.append(r)
        except (ValueError, TypeError):
            continue
    
    for r in filtered_restaurants:
        try:
            rating = float(r.get("rating", 0))
            review_count = int(r.get("reviewCount", 0))
            score = 0.6 * rating + 0.4 * math.log(review_count + 1)
            r["score"] = score
        except (ValueError, TypeError):
            r["score"] = 0
    
    top_restaurants = sorted(filtered_restaurants, key=lambda r: r.get("score", 0), reverse=True)[:10]
    
    place_ids = [r["placeId"] for r in top_restaurants]
    return place_ids
