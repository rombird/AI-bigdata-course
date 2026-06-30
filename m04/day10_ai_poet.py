from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI() # 모델

# 프롬프트 템플릿 생성
prompt = ChatPromptTemplate.from_messages([
    ('system', 'You are helpful assistant.'),
    ('user', '{input}')
])
output_parser = StrOutputParser() # 문자열 출력 파서

chain = prompt | llm | output_parser # 체인구성

st.title('인공지능 시인') # 제목

# 시 주제 입력
content = st.text_input('시의 주제를 제시해주세요.')
st.write('시의 주제는', content)

# 시 작성 요청하기
if st.button('시 작성 요청하기'):
    with st.spinner('Wait for it...'):
        result = chain.invoke({'input':f'{content}에 대한 시를 써줘.'})
        st.write(result)