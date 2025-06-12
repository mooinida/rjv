import httpx
import os
from dotenv import load_dotenv
# time, json, base64 임포트 제거

load_dotenv()

SPRING_SERVER = "http://localhost:8080" # <-- 동일하게 localhost 또는 mooin.shop:8080

# --- 토큰 관리 변수 (단순화: Access Token만 사용) ---
# 전역 변수 ACCESS_TOKEN, REFRESH_TOKEN, TOKEN_EXPIRY_TIME 제거
# 매번 os.getenv("JWT_TOKEN")으로 최신 토큰을 읽어옵니다.

# --- httpx 버전 인증 요청 함수 (토큰 갱신 제거) ---
async def _make_authenticated_request_httpx(method, url, json_data=None, params=None):
    # JWT_TOKEN 환경 변수에서 현재 Access Token 로드
    current_access_token = os.getenv("JWT_TOKEN")
    
    if not current_access_token:
        raise RuntimeError("Authentication required: Access Token is not set. Please log in manually.")

    headers = {
        "Authorization": f"Bearer {current_access_token}",
        "Content-Type": "application/json"
    }

    print(f"🌍 Requesting URL: {url}")
    print(f"📦 Payload: {json_data}")
    print(f"🔐 Headers (Authorization token masked): {{'Content-Type': '{headers.get('Content-Type')}', 'Authorization': 'Bearer ...'}}" )

    try:
        async with httpx.AsyncClient() as client:
            if method == "POST":
                response = await client.post(url, json=json_data, headers=headers, params=params, timeout=15)
            elif method == "GET":
                response = await client.get(url, headers=headers, params=params, timeout=15)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response
    except httpx.RequestError as e:
        print(f"❌ API call to {url} failed: {e}")
        if e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        
        # 401 오류는 Access Token 만료/무효 가능성이 높으므로 RuntimeError로 전환
        if e.response is not None and e.response.status_code == 401:
            raise RuntimeError(f"Authentication required: API call failed with 401. Access Token invalid/expired.")
        else:
            raise

async def get_review_texts(place_id: str) -> list:
    url = f"{SPRING_SERVER}/api/restaurants/{place_id}/review-texts"
    try:
        response = await _make_authenticated_request_httpx("GET", url)
        raw_texts = response.json()
        return [{"text": t} for t in raw_texts]
    except RuntimeError as e:
        print(f"Failed to get review texts due to authentication: {e}")
        return [{"text": f"리뷰 텍스트를 불러오지 못함: 인증 필요."}]
    except httpx.RequestError as e:
        return [{"text": f"리뷰 텍스트 요청 실패: {e}"}]
