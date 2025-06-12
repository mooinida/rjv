from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware # CORS 미들웨어 추가
import asyncio
import os
import sys
from dotenv import load_dotenv

# --- LangGraph 프로젝트 경로 설정 ---
# 중요: 이 경로는 KT 클라우드 서버에서 실제 rjv 프로젝트의 'app' 디렉토리가 있는 경로를 가리켜야 합니다.
# 예를 들어, rjv 프로젝트가 ~/rjv/app 에 있다면:
LANGGRAPH_PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'rjv', 'app'))
sys.path.append(LANGGRAPH_PROJECT_PATH)
print(f"LangGraph project path added to sys.path: {LANGGRAPH_PROJECT_PATH}")


# --- 기존 LangGraph Runner 및 관련 모듈 임포트 ---
try:
    # langGraphRunner.py에서 LangGraph 실행 함수를 임포트
    from agent.langGraphRunner import run_recommendation_pipeline
    # JWT 토큰 관리 함수들을 bring_to_server.py에서 가져옵니다.
    # 이 변수/함수들은 LangGraph가 Spring API를 호출할 때 사용됩니다.
    from bring_to_server import ACCESS_TOKEN, REFRESH_TOKEN, refresh_access_token_if_needed
    from service.get_menu import refresh_access_token_if_needed_httpx as refresh_get_menu_token
    from service.review_fetch import refresh_access_token_if_needed_httpx as refresh_review_token

    print("LangGraph modules loaded successfully.")
except ImportError as e:
    print(f"Error importing LangGraph modules: {e}")
    print(f"Please ensure your LangGraph project (expected at {LANGGRAPH_PROJECT_PATH}) is correctly configured and accessible.")
    sys.exit(1) # 모듈 로드 실패 시 FastAPI 앱 실행 중단

app = FastAPI()

# --- CORS 설정 ---
# 프론트엔드 도메인(개발 서버 및 배포 서버)을 허용해야 합니다.
origins = [
    "http://localhost:5173", # React 개발 서버 포트 (Vite 기본값)
    "http://mooin.shop:8080", # 당신의 프론트엔드 배포 주소 (Spring Boot 백엔드와 동일 포트 사용 시)
    # 프로덕션 배포 시 실제 프론트엔드 도메인을 여기에 추가합니다.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # 모든 HTTP 메서드 허용
    allow_headers=["*"], # 모든 헤더 허용 (Authorization 헤더 포함)
)

# --- 환경 변수 로드 ---
# FastAPI 프로젝트의 .env 파일을 로드합니다. (주로 JWT_TOKEN, REFRESH_TOKEN이 여기에 있어야 합니다.)
load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), '.env')))
print("FastAPI .env file loaded.")

# --- JWT 토큰 검증 및 갱신 미들웨어 ---
# 프론트엔드로부터 받은 토큰을 검증하고, LangGraph 모듈의 전역 변수를 업데이트하며,
# 필요시 Access Token을 갱신합니다.
@app.middleware("http")
async def verify_jwt_token(request: Request, call_next):
    # /api/langgraph로 시작하는 경로에만 인증 로직 적용
    if request.url.path.startswith("/api/langgraph"):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            print("Unauthorized: Missing or invalid token format.")
            return JSONResponse(status_code=401, content={"detail": "Unauthorized: Missing or invalid token"})

        token = auth_header.split(" ")[1]

        # --- LangGraph 모듈 내의 전역 토큰 변수 업데이트 ---
        # 이렇게 하면 langGraphRunner.py 내부의 API 호출 시 이 토큰이 사용됩니다.
        # 이 부분은 TokenManager 클래스를 만들 경우 더 깔끔해집니다.
        os.environ["JWT_TOKEN"] = token # LangGraph 모듈이 os.getenv()로 읽을 수 있도록 업데이트
        global ACCESS_TOKEN, REFRESH_TOKEN, TOKEN_EXPIRY_TIME # bring_to_server.py의 전역 변수 직접 업데이트
        ACCESS_TOKEN = token # 현재 요청의 Access Token을 설정

        # REFRESH_TOKEN은 FastAPI 앱 시작 시점에 .env에서 로드된 값을 유지하며,
        # Refresh Token 갱신 함수에서 사용됩니다.

        # --- Access Token 유효성 검사 및 갱신 시도 ---
        # API 요청 시마다 토큰이 유효한지 확인하고 갱신 시도
        try:
            # requests 기반의 토큰 갱신 로직 실행 (bring_to_server.py)
            if not refresh_access_token_if_needed():
                 return JSONResponse(status_code=401, content={"detail": "Unauthorized: Access token expired or refresh failed."})

            # httpx 기반의 토큰 갱신 로직 실행 (get_menu.py, review_fetch.py)
            # await refresh_get_menu_token()와 await refresh_review_token()은
            # 각 모듈 내에서 해당 함수가 호출될 때 자동으로 갱신 로직이 포함되어 있으므로,
            # 이 미들웨어에서 직접 호출할 필요는 없습니다.
            # 다만, 초기 Access Token이 유효한지 여기서 확인하는 것은 좋습니다.

        except RuntimeError as e:
            # refresh_access_token_if_needed 내부에서 발생하는 인증 관련 RuntimeError
            print(f"Token refresh failed during middleware processing: {e}")
            return JSONResponse(status_code=401, content={"detail": f"Unauthorized: Token refresh failed ({e})."})
        except Exception as e:
            print(f"Unexpected error during token middleware processing: {e}")
            return JSONResponse(status_code=500, content={"detail": "Internal server error during authentication."})

    # 다음 미들웨어 또는 라우터 핸들러로 요청 전달
    response = await call_next(request)
    return response

# --- LangGraph API 엔드포인트 ---
@app.post("/api/langgraph/invoke")
async def invoke_langgraph_api(request_data: Request):
    try:
        data = await request_data.json()
        user_input = data.get("user_input")

        if not user_input:
            raise HTTPException(status_code=400, detail="user_input is required")

        # LangGraph 실행 (langGraphRunner.py의 함수 호출)
        state = {"user_input": user_input}
        langgraph_result = await run_recommendation_pipeline(state)

        # LangGraph 실행 결과 처리
        if "error" in langgraph_result and langgraph_result["error"] == "Authentication required. Please log in manually.":
            # LangGraph 내부에서 인증 오류가 발생한 경우 (예: Refresh Token도 만료)
            return JSONResponse(status_code=401, content={"detail": "Authentication required: Please re-login."})
        elif "error" in langgraph_result:
            # 그 외 LangGraph 내부 오류
            return JSONResponse(status_code=500, content={"detail": langgraph_result["error"]})

        # 성공 응답 반환
        return {"result": langgraph_result.get("result", "응답 없음")}

    except RuntimeError as e: # 미들웨어에서 처리되지 않은 인증 관련 RuntimeError
        return JSONResponse(status_code=401, content={"detail": f"Authentication required: {e}"})
    except Exception as e:
        print(f"Unhandled exception in LangGraph API: {e}")
        return JSONResponse(status_code=500, content={"detail": f"LangGraph execution failed: {e}"})

# --- FastAPI 서버 실행 정보 ---
# 이 부분은 `uvicorn` 명령어로 서버를 시작할 때 필요하며, `main.py` 파일 자체에는 포함되지 않습니다.
# Uvicorn은 `main.py` 파일을 로드하고 `app` 객체를 실행합니다.
# 예시: uvicorn main:app --host 0.0.0.0 --port 5000
