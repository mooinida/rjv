from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
import json
import re
from dotenv import load_dotenv
import requests
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-pro", google_api_key=GOOGLE_API_KEY)

def get_location_and_context(text: str):
    prompt = PromptTemplate.from_template(
    """다음 문장에서 식당의 분위기, 식당을 가는 목적, 입력자의 상황 중에 해당되는것 모두를 추출해줘.
        장소, 음식에 관련된건 추출 하지마. 오로지 분위기, 환경 등.
        ----------------------------------------------
        
        문장: {text}
        
        ----------------------------------------------
        답변형식:
        {{
            "keywords": ["혼밥", "조용한", "가볍게 한잔"]
        }}
        """
    )
    chain = prompt | llm
    result = chain.invoke({"text": text})
    try:
        json_str = re.search(r'\{.*\}', result.content, re.DOTALL)
        if json_str:
            data = json.loads(json_str.group())
            keywords = data.get("keywords", [])
            print(keywords)
            return keywords
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 실패: {e}")

    return "", []

def get_location_and_menu(text: str):
    prompt = PromptTemplate.from_template(
    """다음 문장에서 음식 키워드를 추출해줘.
        최대한 짧은 단위로 나눠.
        쓸모없는 키워드는 제거.
        ex)매운 음식-> 매운, 초밥집->초밥, 고깃집->고기.
        ----------------------------------------------
        
        문장: {text}
        
        ----------------------------------------------
        답변형식:
        {{
            "keywords": ["짜장면", "짬뽕", "중식"]
        }}
        """
    )
    chain = prompt | llm
    result = chain.invoke({"text": text})
    try:
        json_str = re.search(r'\{.*\}', result.content, re.DOTALL)
        if json_str:
            data = json.loads(json_str.group())
            keywords = data.get("keywords", [])
            print(keywords)
            return keywords
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 실패: {e}")

    return "", []

def get_location_from_text(text: str) -> str:
    prompt = PromptTemplate.from_template(
    "다음 문장에서 장소명(예: 지역, 건물, 역 등)만 정확히 추출해줘. 설명하지 말고 장소명만 말해 .문장: {text}"
    )
    chain = prompt | llm
    result = chain.invoke({"text": text})
    location = result.content.strip()
    print(location)
    return location

def get_coordinates_from_location(location: str) -> str: 
    """
    장소명을 위도, 경도로 변환합니다. (예: 성신여자대학교 → 37.5928015,127.0166047)
    Google Maps Geocoding API 사용
    """
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": location,
        "key": GOOGLE_API_KEY,
    }
   
    try:
        response = requests.get(url, params=params)
        data = response.json()

        if data.get("status") == "OK" and data.get("results"):
            location_data = data["results"][0].get("geometry", {}).get("location", {})
            lat = location_data.get("lat")
            lng = location_data.get("lng")
            if lat is not None and lng is not None:
                return {
                    "latitude": lat, "longitude": lng
                }
            else:
                return {"error": "위도 또는 경도 정보가 없습니다."}
        else:
            return {
                "error": f"API 실패: {data.get('status')}, {data.get('error_message', '원인 미상')}"
            }
    except Exception as e:
        return {"error": f"예외 발생: {str(e)}"}
    

SPRING_SERVER = "http://mooin.shop:8080"
JWT_TOKEN = os.getenv("JWT_TOKEN")
def get_nearby_restaurants_DB(latitude: float, longitude: float, radius: int) -> dict:
    params = {
        "lat": latitude,
        "lng": longitude,
        "radius": radius
    }
    url = f"{SPRING_SERVER}/api/restaurants"
    headers = {"Authorization": f"Bearer {JWT_TOKEN}"}
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            return {"restaurants": data} 
        else:
            return {"restaurants": None}
    except Exception as e:
        return {"error": f"예외 발생: {str(e)}"}
    


def findall_restaurants_DB() -> dict:
    url = f"{SPRING_SERVER}/api/restaurants/all"
    headers = {"Authorization": f"Bearer {JWT_TOKEN}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return {"restaurants": data}  
        else:
            return {"restaurants": None}
    except Exception as e:
        return {"error": f"예외 발생: {str(e)}"}
    
    

def next_tool(user_input: str):
    prompt = PromptTemplate.from_template("""
        다음은 사용자의 요청입니다: "{user_input}"

        당신은 아래 도구 중 하나만 선택해야 합니다. 반드시 이름으로만 응답하세요.

        - restart: 추천을 처음부터 다시 시작
        - another_restaurants: 기존 조건으로 다른 식당 추천
        - another_menu: 다른 메뉴 조건으로 추천
        - show_menu: 현재 식당의 메뉴 확인

        반드시 위 네 개 중 하나만 이름만 단독으로 출력하세요.
        """
    )
    chain = prompt | llm
    result = chain.invoke({"user_input":user_input})
    tool_name = result.content.strip().lower()
    print("🔀 분기 도구:", tool_name)
    return {
        "restart": "location_node",
        "show_menu": "menu_node",
        "another_restaurants": "intersection_node",
        "another_menu": "menu_node",
    }.get(tool_name, "end")
