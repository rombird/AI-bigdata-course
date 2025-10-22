from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import streamlit as st
import tempfile
import os
from dotenv import load_dotenv
load_dotenv()


# 제목
st.title('ChatPDF')
st.write('---') # 구분선

# 파일 업로드
uploaded_file = st.file_uploader('PDF 파일을 올려주세요!', type=['pdf'])
st.write('---')

# 사용자 함수 정의
def pdf_to_document(uploaded_file):
    """사용자가 업로드한 파일을 불러오는 함수"""
    temp_dir = tempfile.TemporaryDirectory() # 임시 폴더
    temp_filepath = os.path.join(temp_dir.name, uploaded_file.name)
    with open(temp_filepath, 'wb') as f:
        f.write(uploaded_file.getvalue())
    loader = PyPDFLoader(temp_filepath)
    pages = loader.load_and_split()
    return pages

# 사용자가 파일을 업로드했을 경우에만 실행하도록!
if uploaded_file is not None:
    pages = pdf_to_document(uploaded_file)
    # 텍스트 분할
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 300,
        chunk_overlap=20,
        length_function=len,
        is_separator_regex=False,
    )
    texts = text_splitter.split_documents(pages)

    # 임베딩
    embeddings_model = OpenAIEmbeddings(
        model='text-embedding-3-large',
    )

    # 벡터 db -> 크로마
    db = Chroma.from_documents(texts, embeddings_model)

    # 사용자 입력
    st.header('ChatPDF에게 질문해보세요!!!')
    question = st.text_input('질문을 입력하세요')

    # 질문하기 버튼을 클릭했을 때 실행
    if st.button('질문하기'):
        with st.spinner('Wait for it...'):
            llm = ChatOpenAI(temperature=0)
            # 검색기
            retriever_from_llm = MultiQueryRetriever.from_llm(
                retriever = db.as_retriever(), llm=llm
            )

            # 프롬프트 템플릿
            prompt = hub.pull('rlm/rag-prompt')

            # 결과 포맷 생성
            def format_docs(docs):
                return '\n\n'.join(doc.page_content for doc in docs)
            
            # 체인
            rag_chain = (
                {'context': retriever_from_llm | format_docs,
                 'question': RunnablePassthrough()}
                 | prompt
                 | llm
                 | StrOutputParser()
            )
            result = rag_chain.invoke(question)
            st.write(result)