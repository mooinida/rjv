# app/bring_to_server.py

import requests
import os
import httpx

SPRING_SERVER = "http://localhost:8080" # 또는 배포 서버 주소

def _make_authenticated_request(method, url, json_data=None, params=None):
    """
    환경변수에서 JWT 토큰을 가져와 동기(sync) 요청을 보내는 헬퍼 함수
    """
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

async def _make_async_authenticated_request(method, url, json_data=None, params=None):
    """
    환경변수에서 JWT 토큰을 가져와 비동기(async) 요청을 보내는 헬퍼 함수
    """
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

# --- 실제 호출 함수들 ---

def bring_nearby_restaurants(latitude: float, longitude: float, radius: int) -> dict:
    url = f"{SPRING_SERVER}/api/restaurants"
    params = {"lat": latitude, "lng": longitude, "radius": radius}
    response = _make_authenticated_request("GET", url, params=params)
    return {"restaurants": response.json()}

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

async def get_menu_texts(place_id: int) -> list:
    url = f"{SPRING_SERVER}/api/restaurants/{place_id}/menus"
    response = await _make_async_authenticated_request("GET", url)
    return response.json()
    
async def get_review_texts(place_id: int) -> list:
    url = f"{SPRING_SERVER}/api/restaurants/{place_id}/reviews"
    response = await _make_async_authenticated_request("GET", url)
    return response.json()
