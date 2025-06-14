# bring_to_server.py

import requests
import os
import httpx

# .env 파일에서 환경변수를 로드하는 것은 main.py에서 이미 처리했으므로 여기서는 불필요
# from dotenv import load_dotenv
# load_dotenv() 

SPRING_SERVER = "http://localhost:8080"  # 또는 http://mooin.shop:8080

def _make_authenticated_request(method, url, json_data=None, params=None):
    """
    os.getenv("JWT_TOKEN")를 사용하여 인증 요청을 보내는 헬퍼 함수
    """
    # FastAPI 미들웨어에서 설정해준 환경 변수에서 토큰을 가져옵니다.
    current_access_token = os.getenv("JWT_TOKEN")
    
    if not current_access_token:
        raise RuntimeError("인증 토큰이 없습니다. 로그인 상태를 확인하세요.")

    headers = {
        "Authorization": f"Bearer {current_access_token}",
        "Content-Type": "application/json"
    }

    try:
        if method.upper() == "POST":
            response = requests.post(url, json=json_data, headers=headers, params=params, timeout=15)
        elif method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=15)
        else:
            raise ValueError(f"지원하지 않는 HTTP 메소드: {method}")

        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        if e.response is not None and e.response.status_code == 401:
            raise RuntimeError(f"인증에 실패했습니다(401). 토큰이 만료되었거나 유효하지 않습니다.")
        raise e

def bring_menu_filter_restaurants(keywords: list):
    url = f"{SPRING_SERVER}/api/restaurants/filter/menu"
    response = _make_authenticated_request("POST", url, json_data={"keywords": keywords})
    return {"restaurants": response.json()}

def bring_context_filter_restaurants(contexts: list):
    url = f"{SPRING_SERVER}/api/restaurants/filter/context"
    response = _make_authenticated_request("POST", url, json_data={"keywords": contexts})
    return {"restaurants": response.json()}

def bring_rating_count(placeIds: list):
    url = f"{SPRING_SERVER}/api/restaurants/ratingAndCount"
    response = _make_authenticated_request("POST", url, json_data=placeIds)
    return {"restaurants": response.json()}

def bring_restaurants_list(placeIds: list):
    url = f"{SPRING_SERVER}/api/restaurants/restaurants"
    response = _make_authenticated_request("POST", url, json_data=placeIds)
    return {"restaurants": response.json()}

# --- 비동기 함수들 ---
async def _make_async_authenticated_request(method, url, json_data=None, params=None):
    current_access_token = os.getenv("JWT_TOKEN")
    if not current_access_token:
        raise RuntimeError("인증 토큰이 없습니다. 로그인 상태를 확인하세요.")

    headers = {"Authorization": f"Bearer {current_access_token}", "Content-Type": "application/json"}
    
    async with httpx.AsyncClient() as client:
        try:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=params, timeout=15)
            elif method.upper() == "POST":
                 response = await client.post(url, json=json_data, headers=headers, params=params, timeout=15)
            else:
                 raise ValueError(f"지원하지 않는 HTTP 메소드: {method}")
            
            response.raise_for_status()
            return response
        except httpx.RequestError as e:
            if e.response is not None and e.response.status_code == 401:
                raise RuntimeError(f"인증에 실패했습니다(401). 토큰이 만료되었거나 유효하지 않습니다.")
            raise e

async def get_menu_texts(place_id: int) -> list:
    url = f"{SPRING_SERVER}/api/restaurants/{place_id}/menus"
    response = await _make_async_authenticated_request("GET", url)
    return response.json()
    
async def get_review_texts(place_id: int) -> list:
    url = f"{SPRING_SERVER}/api/restaurants/{place_id}/reviews"
    response = await _make_async_authenticated_request("GET", url)
    return response.json()
