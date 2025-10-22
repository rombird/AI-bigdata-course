# poetry add wikipedia
# poetry add arxiv

# Agent 생성을 위해
from langchain.agents import AgentExecutor

# agent에게 전달하기 위한 tool 생성
from langchain.agents import create_openai_tools_agent

# 미리 만들어진 프롬프트 가져오기 위해서
from langchain import hub

# arxiv 논문 검색을 위한 tool 생성(arxiv API를 사용해서 논문 검색하는 도구)
from langchain_community.utilities import ArxivAPIWrapper
from langchain_community.tools import ArxivQueryRun

# 벡터 DB 구축 및 검색 도구
from langchain.tools.retriever import create_retriever_tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import WebBaseLoader

# agent tools 중에서 wikipedia 사용하기 위해
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import WikipediaQueryRun

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

openai = ChatOpenAI(
    model='gpt-4o-mini', temperature=0.1
)

prompt = hub.pull('hwchase17/openai-functions-agent')

# wikipedia
# top_k_results --> 결과 개수
# doc_content_chars_max --> 글자 길이 제한
api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=200)
wiki = WikipediaQueryRun(api_wrapper=api_wrapper)
# print(wiki)
# print(wiki.name) # wikipedia

# 네이버 뉴스 로딩 및 문서 분할
loader = WebBaseLoader('https://news.naver.com/') # 네이버 뉴스
docs = loader.load() # 웹 문서를 불러와서 저장

documents = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
).split_documents(docs)

# 문서를 임베딩하고 chroma 벡터 DB로 저장
vectordb = Chroma.from_documents(documents, OpenAIEmbeddings())
retriever = vectordb.as_retriever()

print(retriever)

# 검색 도구 생성
retriever_tool = create_retriever_tool(
    retriever, 'naver_news_search', '네이버 뉴스 정보가 저장된 벡터 DB, 당일 기사에 대해서 궁금하면 이 툴을 사용하세요!'
)
# print(retriever_tool)
# print(retriever_tool.name) # naver_news_search

# arxiv tool
arxiv_wrapper = ArxivAPIWrapper(
    top_k_results=1, doc_content_chars_max=200, load_all_available_meta=False
)
arxiv = ArxivQueryRun(api_wrapper=arxiv_wrapper)
# print(arxiv)
# print(arxiv.name) # arxiv

# Agent와 tool(도구) 통합
# agent가 사용한 도구를 정의해서 tools에 저장
# wiki, retriever_tool, arxiv 묶인 tool을 사용
tools = [wiki, retriever_tool, arxiv]

agent = create_openai_tools_agent(
    llm=openai,
    tools=tools,
    prompt=prompt
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True) # 실행과정 출력

# agent_result = agent_executor.invoke({'input':'llm 관련 최신 논문을 알려줘.'})
# agent_result = agent_executor.invoke({'input':'오늘 부동산 관련 주요 소식을 알려줘.'})
agent_result = agent_executor.invoke({'input':'판다에 대해서 설명해줘.'})
print(agent_result)

