import requests
import os
from dotenv import load_dotenv
# time, json, base64 임포트 제거 (만료 시간 파싱 불필요)

load_dotenv()

SPRING_SERVER = "http://localhost:8080" 
# 또는 SPRING_SERVER = "http://mooin.shop:8080" 

# --- 토큰 관리 변수 (단순화: Access Token만 사용) ---
# 전역 변수 ACCESS_TOKEN, REFRESH_TOKEN, TOKEN_EXPIRY_TIME 제거
# 매번 os.getenv("JWT_TOKEN")으로 최신 토큰을 읽어옵니다.

# --- API 호출 함수들 수정 (토큰 갱신 로직 제거) ---
def _make_authenticated_request(method, url, json_data=None, params=None):
    # JWT_TOKEN 환경 변수에서 현재 Access Token 로드
    current_access_token = os.getenv("JWT_TOKEN")
    
    if not current_access_token:
        # 토큰이 없으면 즉시 오류 발생 (인증 필요)
        raise RuntimeError("Authentication required: Access Token is not set. Please log in manually.")

    headers = {
        "Authorization": f"Bearer {current_access_token}", # 로드된 토큰 사용
        "Content-Type": "application/json"
    }
    
    print(f"🌍 Requesting URL: {url}")
    print(f"📦 Payload: {json_data}")
    print(f"🔐 Headers (Authorization token masked): {{'Content-Type': '{headers.get('Content-Type')}', 'Authorization': 'Bearer ...'}}" )

    try:
        if method == "POST":
            response = requests.post(url, json=json_data, headers=headers, params=params, timeout=15)
        elif method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=15)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status() 
        return response
    except requests.exceptions.RequestException as e:
        print(f"❌ API call to {url} failed: {e}")
        if e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        
        # 401 오류는 Access Token 만료/무효 가능성이 높으므로 RuntimeError로 전환
        if e.response is not None and e.response.status_code == 401:
            raise RuntimeError(f"Authentication required: API call failed with 401. Access Token invalid/expired.")
        else:
            raise # 다른 RequestException은 그대로 다시 전달

# 각 API 호출 함수들은 _make_authenticated_request를 사용 (변화 없음)
def bring_menu_filter_restaurants(keywords: list):
    url = f"{SPRING_SERVER}/api/restaurants/filter/menu"
    response = _make_authenticated_request("POST", url, json_data={"keywords": keywords})
    return {"restaurants": response.json()}

def bring_context_filter_restaurants(contexts: list):
    url = f"{SPRING_SERVER}/api/restaurants/filter/context"
    response = _make_authenticated_request("POST", url, json_data={"keywords": contexts})
    return {"restaurants": response.json()}

def bring_restaurants_list(placeIds: list):
    url = f"{SPRING_SERVER}/api/restaurants/restaurants"
    response = _make_authenticated_request("POST", url, json_data=placeIds)
    return {"restaurants": response.json()}

def send_restaurant_rating(place_id: int, rating: float, count: int):
    url = f"{SPRING_SERVER}/api/restaurants/{place_id}/rating"
    payload = {"rating": rating, "reviewCount": count}
    response = _make_authenticated_request("POST", url, json_data=payload)
    return response.status_code, response.text

def send_restaurant(restaurant: dict):
    url = f"{SPRING_SERVER}/api/restaurants"
    response = _make_authenticated_request("POST", url, json_data=restaurant)
    return response.status_code, response.text

def restaurant_is_exist(place_id: int) -> bool:
    try:
        url = f"{SPRING_SERVER}/api/restaurants/{place_id}"
        response = _make_authenticated_request("GET", url)
        return response.ok and response.json()
    except RuntimeError as e: 
        print(f"Authentication required for restaurant_is_exist: {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error checking if restaurant {place_id} exists: {e}")
        return False

def send_reviews(place_id: int, reviews: list):
    url = f"{SPRING_SERVER}/api/restaurants/{place_id}/reviews"
    response = _make_authenticated_request("POST", url, json_data=reviews)
    return response.status_code, response.text

def send_menus(place_id: int, items: list):
    url = f"{SPRING_SERVER}/api/restaurants/{place_id}/menus"
    response = _make_authenticated_request("POST", url, json_data=items)
    return response.status_code, response.text
