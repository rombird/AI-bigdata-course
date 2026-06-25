import pymupdf
# import fitz
import os

# python -m pip install PyMuPDF
pdf_file_path = r'data\과정기반 작물모형을 이용한 웹 기반 밀 재배관리 의사결정 지원시스템 설계 및 구축.pdf'
doc = pymupdf.open(pdf_file_path) # 페이지별로 내용을 읽어온다

header_height = 80 # 헤더 높이 80으로 설정
footer_height = 80 # 푸터 높이 80으로 설정

full_text = ''

# 문서 페이지 반복(각 페이지를 반복하여 텍스트 추출)
for page in doc:
    rect = page.rect # 페이지 크기 가져옴
    # print(rect) # Rect(왼쪽 아래 x,y , 오른쪽 위x,y)
    # print(rect.width) # 페이지 너비 -> 612.0
    # print(rect.height) # 페이지 높이 -> 825.0

    # 텍스트를 추출할 영역 clip으로 지정
    # 헤더
    header = page.get_text(clip=(0, 0, rect.width, header_height))
    # print(header)
    # 푸터
    footer = page.get_text(clip=(0, rect.height - footer_height, rect.width, rect.height))
    # 메인
    text = page.get_text(clip=(0, header_height, rect.width, rect.height-footer_height))
    
    full_text += text + '\n----------------------------------\n' # 페이지 구분하기 위해 점선 추가

# 파일명 추출
pdf_file_name = os.path.basename(pdf_file_path) # 파일명과 확장자(.pdf) 추출
pdf_file_name = os.path.splitext(pdf_file_name)[0] # 파일명만 추출
txt_file_path = f'output/{pdf_file_name}_with_preprocessing.txt' # output폴더에 추출한 내용을 파일명.txt로 내보내는 작업

with open(txt_file_path, 'w', encoding='utf-8') as f:
    f.write(full_text) # txt파일 안에 추출한 모든 내용을 저장




