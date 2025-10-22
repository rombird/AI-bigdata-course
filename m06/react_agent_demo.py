import os
import inspect
from pathlib import Path
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent 

# --- .env 로드: 스크립트 상위 폴더의 .env를 명시적으로 찾고, 기존 env를 덮어쓰기 ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

async def build_agent() -> tuple[object, MultiServerMCPClient]: # 객체, MCPClient가 튜플로 묶어져서 나올 것
    """MCP 클라이언트를 사용하여 React 에이전트 생성"""
    # 1) MCP 클라이언트 (멀티서버)
    client = MultiServerMCPClient({
        # 로컬 stdio 수학 서버 - math.server
        "math" : {
            "command":"python",
            "args":[os.path.abspath("servers/math_server.py")],
            "transport":"stdio",
        },
        # 로컬 stdio 날씨 서버 - weather_server
        "weather" : {
            "command" : "python",
            "args" : [os.path.abspath("servers/weather_server.py")],
            "transport":"stdio",
        }
    })

    # 2) MCP 서버들이 노출한 모든 "툴"을 langchain 도구(툴)로 변환
    tools = await client.get_tools()