from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
load_dotenv()

# 음식 리뷰 평가 AI 만들기

# 평가를 위한 프롬프트 템플릿을 정의
# 사용자의 리뷰를 기반으로 점수 범위를 정한 템플릿을 작성
prompt_template = "이 음식 리뷰 '{review}'에 대해 '{rating1}'점부터 '{rating2}'점까지의 평가를 해주세요."
prompt = PromptTemplate(
    input_variables=['review', 'rating1', 'rating2'], template=prompt_template
)

# 모델 -> gpt-3.5-turbo
# temperature 속성을 설정하여 낮은 값은 보다 일관된 결과를, 높은 값은 다양한 결과를 생성하도록 한다.
openai = ChatOpenAI(model='gpt-3.5-turbo', temperature=0.7)

# 프롬프트와 모델을 연결 -> 체인 구성 : 입력 데이터를 프롬프트에 전달하고 
# 프롬프트를 통해 생성된 데이터를 AI모델에 전달하여 최종 결과를 얻을 수 있다
chain = prompt | openai | StrOutputParser()

# 사용자의 리뷰와 점수 범위를 입력하여 AI모델에게 평가를 요청
# 요청이 성공적이면 결과 출력, 오류 발생할 경우 예외처리를 통해 에러메세지 출력
# 평가 결과는 콘솔에 출력
try:
    with open('review_result_1.txt', 'w', encoding='utf-8') as f:
        response=chain.invoke({
            'review' : '맛은 있었지만 배달 포장 상태가 아쉬웠습니다.',
            'rating1' : '1',
            'rating2' : '5'
        })
        f.write(f'평가 결과 : {response}\n')
        print(f'평가결과가 review_result_1.txt 파일에 저장되었습니다.')
except Exception as e: # Exception(예외)이 가지고 있는 예외 메시지 -> e
    print(f'Error : {e}') # 예외 메시지 e의 내용이 출력

print('-'*50)

with open('review_result_2.txt', 'w', encoding='utf-8') as f:
    response2 = chain.stream({
        'review' : '맛은 있었지만 배달 포장 상태가 아쉬웠습니다.',
        'rating1' : '1',
        'rating2' : '5'
    })
    for token in response2:
        f.write(token)
        print(token, end='', flush=True)
