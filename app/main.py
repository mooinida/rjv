# main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
import sys
from dotenv import load_dotenv

# --- LangGraph 프로젝트 경로 설정 ---
LANGGRAPH_PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(LANGGRAPH_PROJECT_PATH)
print(f"LangGraph project path added to sys.path: {LANGGRAPH_PROJECT_PATH}")

# --- 기존 LangGraph Runner 및 관련 모듈 임포트 ---
try:
    from agent.langGraphRunner import run_recommendation_pipeline # LangGraph 함수 임포트
    # 이제 bring_to_server 등에서 전역 토큰 변수를 임포트할 필요 없음.
    # main.py 미들웨어에서 os.environ["JWT_TOKEN"]을 설정하면 됨.

    print("LangGraph modules loaded successfully.")
except ImportError as e:
    print(f"Error importing LangGraph modules: {e}")
    print(f"Please ensure your LangGraph project (expected at {LANGGRAPH_PROJECT_PATH}) is correctly configured and accessible.")
    sys.exit(1)

app = FastAPI()

# --- CORS 설정 --- (기존과 동일)
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

# --- 환경 변수 로드 --- (기존과 동일)
load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), '.env')))
print("FastAPI .env file loaded.")

# --- JWT 토큰 검증 및 갱신 미들웨어 ---
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
        # os.environ에만 JWT_TOKEN을 설정하면, 다른 모듈들이 os.getenv()로 이 값을 읽습니다.
        os.environ["JWT_TOKEN"] = token 
        
    response = await call_next(request)
    return response

# --- LangGraph API 엔드포인트 --- (기존과 동일)
@app.post("/api/langgraph/invoke")
async def invoke_langgraph_api(request_data: Request):
    try:
        data = await request_data.json()
        user_input = data.get("user_input")

        if not user_input:
            raise HTTPException(status_code=400, detail="user_input is required")

        state = {"user_input": user_input}
        langgraph_result = await run_recommendation_pipeline(state)
        
        if "error" in langgraph_result and "Authentication required" in langgraph_result["error"]:
            return JSONResponse(status_code=401, content={"detail": "Authentication required: Please re-login."})
        elif "error" in langgraph_result:
            return JSONResponse(status_code=500, content={"detail": langgraph_result["error"]})
        
        return {"result": langgraph_result.get("result", "응답 없음")}
    
    except RuntimeError as e: 
        return JSONResponse(status_code=401, content={"detail": f"Authentication required: {e}"})
    except Exception as e:
        print(f"Unhandled exception in LangGraph API: {e}")
        return JSONResponse(status_code=500, content={"detail": f"LangGraph execution failed: {e}"})
