from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
import sys
from dotenv import load_dotenv

# --- LangGraph 프로젝트 경로 설정 ---
# 중요: 이 경로는 KT 클라우드 서버에서 실제 rjv 프로젝트의 'app' 디렉토리가 있는 경로를 가리켜야 합니다.
# main.py 파일이 ~/rjv/app/ 에 있으므로, 현재 디렉토리인 '.'을 sys.path에 추가합니다.
LANGGRAPH_PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(LANGGRAPH_PROJECT_PATH)
print(f"LangGraph project path added to sys.path: {LANGGRAPH_PROJECT_PATH}")

# --- 기존 LangGraph Runner 및 관련 모듈 임포트 (자동 토큰 갱신 관련 제거) ---
try:
    from agent.langGraphRunner import run_recommendation_pipeline
    # JWT 토큰 관리 함수들을 bring_to_server.py에서 가져오되, 갱신 로직 관련은 제외
    # ACCESS_TOKEN은 미들웨어에서 직접 설정하므로 임포트 필요 없음.
    # REFRESH_TOKEN, refresh_access_token_if_needed 등 갱신 관련은 이제 임포트하지 않음.
    
    # 단, bring_to_server.py, get_menu.py, review_fetch.py 내부의
    # _make_authenticated_request / _make_authenticated_request_httpx 함수들은
    # 여전히 전역 ACCESS_TOKEN을 사용하고, 401 시 RuntimeError를 발생시킬 것입니다.
    # 해당 파일들 내부의 토큰 갱신 로직(refresh_access_token_if_needed 등)도 제거해야 합니다.
    # (FastAPI에서는 미들웨어에서 토큰을 설정하고, 하위 모듈은 그 토큰을 사용만 하도록 할 것임)

    print("LangGraph modules loaded successfully (without auto-refresh).")
except ImportError as e:
    print(f"Error importing LangGraph modules: {e}")
    print(f"Please ensure your LangGraph project (expected at {LANGGRAPH_PROJECT_PATH}) is correctly configured and accessible.")
    sys.exit(1)

app = FastAPI()

# --- CORS 설정 ---
origins = [
    "http://localhost:5173", # React 개발 서버 포트 (Vite 기본값)
    "http://mooin.shop:8080", # 당신의 프론트엔드 배포 주소
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 환경 변수 로드 ---
# FastAPI 프로젝트의 .env 파일을 로드합니다. (주로 JWT_TOKEN이 여기에 있어야 합니다.)
load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), '.env')))
print("FastAPI .env file loaded.")

# --- JWT 토큰 검증 미들웨어 ---
# 프론트엔드로부터 받은 Access Token을 LangGraph 모듈에 전달합니다.
@app.middleware("http")
async def verify_jwt_token(request: Request, call_next):
    if request.url.path.startswith("/api/langgraph"):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            print("Unauthorized: Missing or invalid token format.")
            return JSONResponse(status_code=401, content={"detail": "Unauthorized: Missing or invalid token"})

        token = auth_header.split(" ")[1]
        
        # --- LangGraph 모듈의 전역 토큰 변수 업데이트 ---
        # 여기서는 Access Token만 사용하므로 os.environ만 업데이트합니다.
        # 다른 모듈도 os.getenv("JWT_TOKEN")으로 이 토큰을 읽을 것입니다.
        os.environ["JWT_TOKEN"] = token 

        # 실제 JWT 토큰 유효성 검증 (만료 여부, 서명)은 Spring Boot에서 처리
        # FastAPI에서는 토큰을 받아서 LangGraph 모듈로 전달하는 역할만 수행
        
        # (선택 사항: 만료 여부만 간단히 확인하여 빠르게 401 반환)
        # try:
        #     import jwt # PyJWT 라이브러리 필요
        #     decoded_payload = jwt.decode(token, options={"verify_signature": False})
        #     if decoded_payload.get('exp', 0) < time.time():
        #         return JSONResponse(status_code=401, content={"detail": "Unauthorized: Access token expired."})
        # except Exception:
        #     return JSONResponse(status_code=401, content={"detail": "Unauthorized: Invalid token format."})
        
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
        if "error" in langgraph_result and langgraph_result["error"].includes("Authentication required"):
            # LangGraph 내부에서 인증 오류가 발생한 경우
            return JSONResponse(status_code=401, content={"detail": "Authentication required: Please re-login."})
        elif "error" in langgraph_result:
            # 그 외 LangGraph 내부 오류
            return JSONResponse(status_code=500, content={"detail": langgraph_result["error"]})
        
        return {"result": langgraph_result.get("result", "응답 없음")}
    
    except RuntimeError as e: # run_recommendation_pipeline에서 발생한 인증 관련 RuntimeError
        return JSONResponse(status_code=401, content={"detail": f"Authentication required: {e}"})
    except Exception as e:
        print(f"Unhandled exception in LangGraph API: {e}")
        return JSONResponse(status_code=500, content={"detail": f"LangGraph execution failed: {e}"})
