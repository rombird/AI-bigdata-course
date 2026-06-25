from openai import OpenAI
from dotenv import load_dotenv
import os
import pymupdf

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

def pdf_to_text(pdf_file_path: str):
    """PDF 파일을 텍스트로 변환해 저장하는 함수"""
    pdf_file_path = r'data\과정기반_작물모형을_이용한_웹_기반_밀_재배관리_의사결정_지원시스템_설계_및_구축.pdf'
    doc = pymupdf.open(pdf_file_path)  # 페이지별로 내용을 읽어온다

    header_height = 80   # 헤더 높이 (80으로 설정)
    footer_height = 80   # 푸터 높이 (80으로 설정)

    full_text = ''

    for page in doc:  
        rect = page.rect  # 페이지 크기 가져오기
        
        # 텍스트를 추출할 영역을 clip으로 지정
        header = page.get_text(clip=(0, 0, rect.width, header_height))
        footer = page.get_text(clip=(0, rect.height - footer_height, rect.width, rect.height))
        text = page.get_text(clip=(0, header_height, rect.width, rect.height - footer_height))
        
        # full_text에 덧붙일 때 줄 바꿈 표시를 해서 페이지 구분
        full_text += text + '\n--------------------------------------------\n' 
        
        
    # 파일명 추출
    pdf_file_name = os.path.basename(pdf_file_path) 
    pdf_file_name = os.path.splitext(pdf_file_name)[0] # 확장자 제거

    txt_file_path = f'output/{pdf_file_name}_with_preprocessing.txt'  
    with open(txt_file_path, 'w', encoding='utf-8') as f:
        f.write(full_text)
        
    return txt_file_path        
        

def summarize_txt(file_path: str):
    client = OpenAI(api_key=api_key)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        txt = f.read()
        
    # system_prompt에 요약 방법을 담는다. 제목을 먼저 쓰고 저자의 문제 인식과
    # 주장을 15문장이내로 요약하라고 주문한 뒤 저자 소개를 추가하도록 한다.
    # 마지막에 요약을 위해 필요한 txt내용을 추가한다.    
    system_prompt = f'''
    너는 다음 글을 요약하는 봇이다. 아래 글을 읽고, 저자의 문제 인식과
    주장을 파악하고, 주요 내용을 요약하라.
    
    작성해야 하는 포맷은 다음과 같다.
    
    # 제목
    
    ## 저자의 문제 인식 및 주장 (15문장 이내)
    
    ## 저자 소개
    
    ========== 이하 텍스트 ==========
    
    { txt }
    '''
    
    print(system_prompt)
    print('=' * 50)
    
    # gpt-4o모델에 요약을 요청하는 단계
    # (대화 형식으로 멀티턴을 할 필요가 없으므로 role은 system으로 넘겨준다)
    response = client.chat.completions.create(
        model='gpt-4o',
        temperature=0.1,
        messages=[
            {'role':'system', 'content':system_prompt},
        ]
    )
    
    return response.choices[0].message.content

def summarize_pdf(pdf_file_path: str, output_file_path: str):
    """pdf_to_text 함수를 실행한 결과를 summarize_txt 함수에 넣어 실행하는 역할을 하는 함수"""
    txt_file_path = pdf_to_text(pdf_file_path)
    summary = summarize_txt(txt_file_path)
    
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    
if __name__ == '__main__':
    pdf_file_path = f'data\과정기반_작물모형을_이용한_웹_기반_밀_재배관리_의사결정_지원시스템_설계_및_구축.pdf'
    summarize_pdf(pdf_file_path, r'output\crop_model_summary.txt')