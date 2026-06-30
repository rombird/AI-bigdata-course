from day6_gpt_function_1 import get_current_time, tools
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=api_key)

def get_ai_response(messages, tools=None):
    """tools에 get_function의 tools를 대입해주면 get_current_time 함수를 사용할 수 있다."""
    response=client.chat.completions.create(
        model='gpt-4o',
        messages=messages,
        tools=tools,
    )
    return response

messages=[{'role':'system', 'content':'너는 사용자를 도와주는 상담사야'}]

while True:
    user_input = input('사용자\t: ') # 사용자가 질문 입력
    if user_input == 'exit': # 사용자가 'exit'를 입력하면 질문 종료(반복 종료)
        break
    messages.append({'role':'user','content':user_input}) # 사용자 메세지를 대화기록에 추가(기억하도록 저장함)
    ai_response = get_ai_response(messages, tools=tools)
    ai_message = ai_response.choices[0].message 
    print(ai_message) # 임시출력

    # ai_message안에 tool_calls 속성 존재 -> tool_calls가 있다면 함수를 실행해야한다고 GPT가 판단했다는 뜻
    tool_calls = ai_message.tool_calls
    if tool_calls: # tool_calls에 값이 있다면 
        for tool_call in tool_calls:
            tool_name = tool_call.function.name # 실행할 함수명
            tool_call_id = tool_call.id # 펑션 콜링의 id

            arguments = json.loads(tool_call.function.arguments)
            if tool_name == 'get_current_time':
                messages.append(
                    {
                        'role':'function', 
                        'tool_call_id':tool_call_id,
                        'name':tool_name,
                        'content':get_current_time(timezone=arguments['timezone']), # timezone이라는 매개변수 안에 'timezone'이라는 key값 들어감
                    }
                )
        messages.append({
            'role':'system',
            'content':'이제 주어진 결과를 바탕으로 답변할 차례다.'
        })

        ai_response = get_ai_response(messages, tools=tools)
        ai_message = ai_response.choices[0].message
    
    messages.append(ai_message)
    print('AI\t: ' + ai_message.content)