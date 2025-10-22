import os
import tempfile
import streamlit as st
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.prompts import ChatPromptTemplate
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import Chroma
from langchain.load import dumps, loads
from dotenv import load_dotenv

load_dotenv()

st.title('ChatPDF with Multiquery + HybridSearch + RAG-Fusion')
st.write('---')
st.title('PDF 파일을 업로드하고 내용을 기반으로 질문하세요.')

model_choice = st.selectbox(
    '사용할 GPT 모델은 선택하세요 : ',
    ['gpt-3.5-turbo', 'gpt-4o-mini', 'gpt-4o']
)
uploaded_file = st.file_uploader('PDF 파일을 업로드해주세요!', type=['pdf'])
st.write('---')

def pdf_to_document(uploaded_file):
    temp_dir = tempfile.TemporaryDirectory()
    temp_filepath = os.path.join(temp_dir.name, uploaded_file.name)
    with open(temp_filepath, 'wb') as f:
        f.write(uploaded_file.getvalue())
    loader = PyPDFLoader(temp_filepath)
    pages = loader.load_and_split()
    return pages

def format_docs(docs):
    return '\n\n'.join(doc.page_content for doc in docs)

if uploaded_file is not None: # 업로드 파일이 존재한다면
    pages = pdf_to_document(uploaded_file)

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=500,
        chunk_overlap=50
    )
    splits = text_splitter.split_documents(pages)
    embeddings_model = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings_model,
        collection_name='pdf_chunks' # 문서들을 묶은 폴더 개념(여기서는 이름이 pdf_chunks) --> 데이터를 분류해서 관리하기 좋게 하는 라벨

    )
    chroma_retriever = vectorstore.as_retriever(
        search_type='mmr',
        search_kwargs={'k':1, 'fetch_k':4}
    )

    bm25_retriever = BM25Retriever.from_documents(splits)
    bm25_retriever.k = 2
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, chroma_retriever],
        weights=[0.2, 0.8]
    )
    template='''
    당신은 AI 언어 모델 조수입니다. 주어진 사용자 질문에 대해 벡터 데이터베이스에서 
    관련 문서를 검색할 수 있도록 다섯가지 다른 버전을 생성하는 것입니다.
    사용자 질문에 대한 여러 관점을 생성함으로써, 거리 기반 유사성 검색의 한계를
    극복하는 데 도움을 주는 것이 목표입니다.
    각 질문은 새 줄로 구분하여 제공하세요. 원본 질문 : {question}
    '''
    prompt_perspectives = ChatPromptTemplate.from_template(template)
    generate_queries = (
        prompt_perspectives
        | ChatOpenAI(model_name=model_choice, temperature=0)
        | StrOutputParser()
        | (lambda x: [q for q in x.split('\n') if q.strip()]) # 빈 줄 구분
        # 1. for q in x.split('\n') 2. if q.strip() 3. q
    )

    def reciprocal_rank_fusion(results: list[list], k=60, top_n=2):
        fused_scores={}
        for docs in results:
            for rank, doc in enumerate(docs):
                doc_str = dumps(doc)
                fused_scores.setdefault(doc_str, 0)
                fused_scores[doc_str] += 1 / (rank + k)
        reranked_results = [
            (loads(doc), score)
            for doc, score in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True) 
        ]
        return reranked_results[:top_n]
    
    retrieval_chain_rag_fusion = generate_queries | ensemble_retriever.map() | reciprocal_rank_fusion

    template = '''
    다음 맥락을 바탕을 질문에 답변하세요 : 
    
    {context}
    
    질문 : {question}
    '''

    # 최종 체인
    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOpenAI(model_name=model_choice, temperature=0)
    final_rag_chain = (
        {'context' : retrieval_chain_rag_fusion,
         'question' : RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    st.header('PDF에 질문하세요!')
    question = st.text_input('질문을 입력하세요.')

    if st.button('질문하기(ASK)'):
        with st.spinner('답변 생성중!!!'):
            result = final_rag_chain.invoke(question)
            st.write(result) 