from day6_gpt_function_1 import get_current_time, tools
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import streamlit as st

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)


def get_ai_response(messages, tools=None):
    """tools에 gpt_functions의 tools를 대입해주면 get_current_time 함수를 사용할 수 있다."""
    response = client.chat.completions.create(
        model='gpt-4o',
        messages=messages,
        tools=tools,
    )
    return response

# --------------------------------------
# streamlit 부분
# --------------------------------------

# 웹 페이지 제목 설정
st.title("🧚‍♀️ 실시간 timezone AI 상담사") 

# 웹 페이지가 새로고침되어도 대화 기록이 날아가지 않게 스트림릿 저장소 사용(sesstion_state)
if 'messages' not in st.session_state:
    st.session_state['messages']=[
        {
            'role':'system',
            'content':'너는 사용자를 도와주는 상담사야'
        },
    ]

# 저장되어 있는 대화 기록을 화면에 표현(system 메시지는 제외)
for msg in st.session_state.messages:
    if msg['role'] == 'assistant' or msg['role'] == 'user':
        st.chat_message(msg['role']).write(msg['content'])

# 사용자에게 채팅 입력 받기
if user_input := st.chat_input():
    st.session_state.messages.append(
        {
            'role':'user',
            'content':user_input
        }
    )
    st.chat_message('user').write(user_input)

    ai_response = get_ai_response(st.session_state.messages, tools=tools)
    ai_message = ai_response.choices[0].message 
    print(ai_message) # 임시출력

    tool_calls = ai_message.tool_calls
    if tool_calls: # tool_calls에 값이 있다면 
        for tool_call in tool_calls:
            tool_name = tool_call.function.name # 실행할 함수명
            tool_call_id = tool_call.id # 펑션 콜링의 id

            arguments = json.loads(tool_call.function.arguments)
            if tool_name == 'get_current_time':
                st.session_state.messages.append(
                    {
                        'role':'function', 
                        'tool_call_id':tool_call_id,
                        'name':tool_name,
                        'content':get_current_time(timezone=arguments['timezone']), # timezone이라는 매개변수 안에 'timezone'이라는 key값 들어감
                    }
                )
        st.session_state.messages.append({
            'role':'system',
            'content':'이제 주어진 결과를 바탕으로 답변할 차례다.'
        })

        ai_response = get_ai_response(st.session_state.messages, tools=tools)
        ai_message = ai_response.choices[0].message
    st.session_state.messages.append(
        {
            'role':'assistant',
            'content':ai_message.content
        }
    )
    print('AI\t: ' + ai_message.content)
    st.chat_message('assistant').write(ai_message.content)