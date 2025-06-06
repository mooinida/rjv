from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI

from tools.conditional_edges_tools import restart,show_menu,another_menu,another_restaurants

from dotenv import load_dotenv
import os
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

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
