from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')

# OpenAI()로 클라이언트를 생성할 때 입력한 api_key 적용
client = OpenAI(api_key=api_key)

response = client.chat.completions.create(
    model='gpt-4o', # 어떤 모델을 사용할 지 설정
    temperature=0.1, # 숫자가 작을 수록 정확, 무작위성을 조절(1에 가까울수록 창의적)
    messages=[
        {'role':'system', 'content':'You are a helpful assistant.'},
        {'role':'user', 'content':'2022년 월드컵 우승팀은 어디야?'}
    ]
)

print(response)
print('-' * 20)
print(response.choices[0].message.content)

# openAI의 API키로 질문하고 답변받기
# 1. 터미널에서 설치
# python -m pip install openai==1.58.1 
# python -m pip install pyton-dotenv
# 2. .env파일 생성후 OPENAI_API_KEY=api키 붙여넣기
# --> key노출 되지 않게 하는 방법

