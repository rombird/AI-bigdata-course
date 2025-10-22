from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')

# OpenAI()로 클라이언트를 생성할 때 입력한 api_key 적용
client = OpenAI(api_key=api_key)

while True:
    user_input = input('사용자 : ')
    if user_input == 'exit':
        break
    response = client.chat.completions.create(
        model='gpt-4o',
        temperature=0.9,
        messages=[
            {'role':'system', 'content':'너는 사용자를 도와주는 상담사야.'},
            {'role':'user', 'content':user_input}
        ]
    )
    print(f'AI : {response.choices[0].message.content}')