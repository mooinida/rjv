# agent_config.py 파일 내용

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType

from tools.conditional_edges_tools import restart,show_menu,another_menu,another_restaurants

from dotenv import load_dotenv
import os

# .env 파일 경로를 명시적으로 지정
# agent_config.py (app/agent)에서 프로젝트 루트 (rjv)에 있는 .env 파일을 찾아야 하므로
# 현재 파일의 디렉토리(__file__)에서 두 단계 상위 디렉토리로 이동한 후 .env를 찾습니다.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.env'))

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# 디버깅을 위해 GOOGLE_API_KEY가 제대로 로드되었는지 확인하는 코드 추가 (선택 사항)
if GOOGLE_API_KEY is None:
    print("경고: GOOGLE_API_KEY 환경 변수가 로드되지 않았습니다!")
    print(f"'.env' 파일을 찾은 경로: {os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.env')}")
    # 오류를 명확히 하기 위해 여기서 예외를 발생시킬 수도 있습니다.
    # raise ValueError("GOOGLE_API_KEY가 환경 변수에서 로드되지 않았습니다.")
else:
    print("정보: GOOGLE_API_KEY가 성공적으로 로드되었습니다.")
    # 보안을 위해 실제 키 값은 출력하지 않는 것이 좋습니다.
    # print(f"로드된 GOOGLE_API_KEY: {GOOGLE_API_KEY[:5]}...")


llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-pro", google_api_key=GOOGLE_API_KEY, temperature=0.4)


tools = [restart, show_menu, another_restaurants, another_menu]

# Agent 초기화
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent_type=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
    max_iterations = 1
)
