from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')

# OpenAI()로 클라이언트를 생성할 때 입력한 api_key 적용
client = OpenAI(api_key=api_key)

response = client.chat.completions.create(
    model='gpt-4o', # 어떤 모델을 사용할 지 설정
    temperature=0.9, # 숫자가 작을 수록 정확, 무작위성을 조절(1에 가까울수록 창의적)
    messages=[
        {'role':'system', 'content':'너는 유치원 학생이야. 유치원생처럼 답변해줘.'},
        {'role':'user', 'content':'오리'}
    ]
)

print(response)
print('-' * 20)
print(response.choices[0].message.content) # response에서 대답부분