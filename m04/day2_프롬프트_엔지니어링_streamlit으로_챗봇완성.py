import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# (0) 사이드바에서 api_key를 입력하는 부분
with st.sidebar:
    openai_api_key = os.getenv('OPENAI_API_KEY')
    '[Get an OpenAI API key](https://platform.openai.com/account/api-keys)'
    '[View the source code](https://github.com/streamlit/llm-examples/blob/main/Chatbot.py)'
    '[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/streamlit/llm-examples?quickstart=1)'

st.title('💬 ChatBot')

# (1) st.session_state에 'messages'가 없으면 초기값을 설정
if 'messages' not in st.session_state:
    st.session_state['messages'] = [{'role':'assistant', 'content':'How can I help you?'}]

# (2) 대화기록을 출력
for msg in st.session_state.messages:
    st.chat_message(msg['role']).write(msg['content'])

# (3) 사용자 입력을 받아 대화기록에 추가하고 AI응답을 생성
if prompt := st.chat_input(): 
    # 바다코끼리 연산자(:=) : 할당과 반환을 동시에 하는 연산자
    if not openai_api_key:
        st.info('Pleas add your OpenAI API Kyt to continue.')
        st.stop()
    client = OpenAI(api_key=openai_api_key)
    st.session_state.messages.append({'role':'user','content':prompt})
    st.chat_message('user').write(prompt)
    response = client.chat.completions.create(model='gpt-4o', message=st.session_state.messages)
    msg = response.choice[0].message.content
    st.session_state.messages.append({'role':'assistant', 'contente':msg})
    st.chat_message('assistant').write(msg)