# 라이브러리 불러오기
# glob 라이브러리 : 파일경로나 이름 패턴을 기반으로 쉽고 
# 직관적으로 파일을 검색할 수 있어, 복잡한 디렉토리 탐색이 필요할 때 매우 유용한 라이브러리
# glob.glob(pattern, recursive=False) : pattern에 와일드 카드 패턴을 지정하며 매칭되는 경로목록을 리스트로 반환
from glob import glob
from openai import OpenAI
from dotenv import load_dotenv
import os
import base64

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

def encode_image(image_path):
    """이미지 파일을 읽어 base64 문자열로 변환하는 함수"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def image_quiz(image_path, n_trial=0, max_trial=3):
    """이미지 경로를 받아 퀴즈를 만드는 함수"""
    if n_trial >= max_trial: # 최대 문제 생성횟수를 넘어서면 예외발생
        raise Exception('Failed to generate a quiz.')
    
    # base64로 이미지 인코딩     
    base64_image = encode_image(image_path)


    quiz_prompt = """
    제공된 이미지를 바탕으로, 다음과 같은 양식으로 퀴즈를 만들어주세요. 
    정답은 1~4 중 하나만 해당하도록 출제하세요.
    토익 리스닝 문제 스타일로 문제를 만들어주세요.
    아래는 예시입니다. 
    ----- 예시 -----

    Q: 다음 이미지에 대한 설명 중 옳지 않은 것은 무엇인가요?
    - (1) 베이커리에서 사람들이 빵을 사고 있는 모습이 담겨 있습니다.
    - (2) 맨 앞에 서 있는 사람은 빨간색 셔츠를 입고 있습니다.
    - (3) 기차를 타기 위해 줄을 서 있는 사람들이 있습니다.
    - (4) 점원은 노란색 티셔츠를 입고 있습니다.

    Listening: Which of the following descriptions of the image is incorrect?
    - (1) It shows people buying bread at a bakery.
    - (2) The person standing at the front is wearing a red shirt.
    - (3) There are people lining up to take a train.
    - (4) The clerk is wearing a yellow T-shirt.
        
    정답: (4) 점원은 노란색 티셔츠가 아닌 파란색 티셔츠를 입고 있습니다.
    (주의: 정답은 1~4 중 하나만 선택되도록 출제하세요.)
    ======
    """

    messages=[
        {
            'role':'user',
            'content':[
                {
                    'type':'text',
                    'text':quiz_prompt
                },
                {
                    'type':'image_url',
                    'image_url':{
                        'url':f'data:image/jpeg;base64, {base64_image}'
                        },
                },
            ],
        }
    ]

    # try ~ except => 예외 처리 구문
    try: # 정상적이면 gpt모델을 이용해서 응답 받는다.
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=messages
        )
    except Exception as e: # 예외(오류)가 발생하면 image_quiz 함수 호출
        print(f'failed\n + {str(e)}')
        return image_quiz(image_path, n_trial+1) # 재귀함수 호출
    
    content = response.choices[0].message.content # 응답 결과를 content변수에 저장

    # Listening이라는 글자가 content안에 포함되어 있다면 
   
    if 'Listening' in content:
        return content, True
    else:  # Listening이라는 글자가 content안에 없다면 다시 image_quiz함수 불러옴->함수 호출해서 gpt모델이 생성하도록
        return image_quiz(image_path, n_trial+1)
    
# 이미지 한장을 넣어서 테스트해보자 -> 함수호출
q = image_quiz('images/busan_dive.jpg')
print(q)