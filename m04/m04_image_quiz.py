# 라이브러리 불러오기
# glob 라이브러리 : 파일경로나 이름 패턴을 기반으로 쉽고 
# 직관적으로 파일을 검색할 수 있어, 복잡한 디렉토리 탐색이 필요할 때 매우 유용한 라이브러리
# glob.glob(pattern, recursive=False) : pattern에 와일드 카드 패턴을 지정하며 매칭되는 경로목록을 리스트로 반환
from glob import glob
from openai import OpenAI
from dotenv import load_dotenv
import os
import base64
import json

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

# emcode_image(image_path)함수
# base64문자열은 OpenAI API 이미지 데이터를 전달할 때 사용

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
    
    content = response.choices[0].message.content
        
    if 'Listening:' in content:
        return content, True
    else:
        return image_quiz(image_path, n_trial+1)

# 여러 문제를 불러오기 위한 코드
# 마크다운 파일 생성 -> .md
# TTS(글자 -> 말) 인식을 위해서 json파일 생성 -> .json


# 문제들을 계속 붙여 나가기 위해 빈 문자열 선언
txt = ""    
eng_dict = [] # 영어 문제만 담기 위해 생성
no = 1 # 문제 번호를 1로 초기화

# images폴더 내의 모든 jpg 파일을 사용
for g in glob('./images/*.jpg'): 
    q, is_suceed = image_quiz(g) # image_quiz내 변수 두개, g : 이미지 객체 1개

    # 문제 생성에 실패하면 다음 문제로 넘어간다.
    if not is_suceed:
        continue # 다음 이미지로 넘어간다(다시 위로 올라감)
    divider = f'## 문제 {no}\n\n'
    print(divider) 
    txt += divider

    # 파일명을 추출해 이미지 링크 만들기
    filename = os.path.basename(g) # 마크다운에 표시할 이미지 파일경로 설정
    txt += f'![image]({filename})\n\n' # 마크다운에서 링크경로

    # 문제 추가
    print(q)
    # txt 문자열 변수에 마크다운 코드가 계속 추가된다.
    txt += f'{q}\n\n----------------------\n\n'

    # 마크다운 파일로 저장
    with open('./images/image_quiz_eng.md', 'w', encoding='utf-8') as f:
        f.write(txt)

    # 영어 문제만 추출
    # .split() -> 괄호 안 내용 기준 분리 -> 결과가 리스트 형태
    # .strip() -> 공백 앞뒤로 제거
    eng = q.split('Listening: ')[1].split('정답: ')[0].strip() # Listening: 을 기준으로 왼쪽 0번, 오른쪽 1번

    eng_dict.append({
        'no':no,
        'eng':eng,
        'img':filename
    })

    # json파일로 저장
    with open('./images/image_quiz_eng.json', 'w', encoding='utf-8') as f:
        json.dump(eng_dict, f, ensure_ascii=False, indent=4)
    
    no += 1 # 문제 번호 증가

