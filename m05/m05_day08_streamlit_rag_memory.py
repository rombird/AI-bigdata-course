import streamlit as st
from dotenv import load_dotenv
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories.streamlit import StreamlitChatMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain

import os


load_dotenv()

# PDF 문서 로드 및 벡터화 함수

# @st.cache_resource : streamlit라이브러리에서 사용하는 데코레이터, 해당 함수의 리턴값을 한번만 계산해서 캐싱하고 다시 실행하지 않도록 ->무거운 리소스를 반복해서 만들지 않도록 성능 최적화를 위해 사용
# st안에 cache_resource 가져오겠다는 뜻
# 한번 실행한 결과 캐싱해서 재실행시 빠르게 로드
@st.cache_resource 
def load_and_split_pdf(file_path):
    """PDF 로드 함수"""
    loader = PyPDFLoader(file_path)
    return loader.load_and_split() # 문서 불러옴

# 이 변수는 외부에서 직접 사용할 필요가 없는 내부용
# _docs는 외부 사용자가 신경 쓰지 않아도 되는 내부 전처리 결과물일 수 있음
@st.cache_resource
def create_vector_store(_docs): # 변수명에 언더바를 붙이면 다른 곳에서 접근못하게 막아두는 역할
    """ 텍스트 청크들을 Chroma_db 안에 임베딩 벡터로 저장"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=0
    )
    split_docs = text_splitter.split_documents(_docs)
    persist_directory = './chroma_db' 
    vectorstore = Chroma.from_documents(
        split_docs,
        OpenAIEmbeddings(model='text-embedding-3-small'),
        persist_directory=persist_directory
    )
    return vectorstore

@st.cache_resource
def get_vectorstore(_docs):
    """만약 기존에 저장해둔 벡터 DB가 있는 경우 이를 불러온다(로드)"""
    persist_directory = './chroma_db' 
    if os.path.exists(persist_directory): # 폴더가 존재한다면 임베딩 해서 return
        return Chroma(
            persist_directory=persist_directory,
            embedding_function=OpenAIEmbeddings(model='text-embedding-3-small')
        )
    else:
        return create_vector_store(_docs)
    
# 메모리 기능이 추가된 RAG 체인 구성 함수

# PDF 문서 로드-벡터 저장-검색기-히스토리 모두 합친 chain 구축
@st.cache_resource
def initialize_components(selected_model):
    file_path= './대한민국헌법(헌법)(제00010호)(19880225).pdf'
    pages = load_and_split_pdf(file_path)
    vectorstore = get_vectorstore(pages)
    retriever = vectorstore.as_retriever()


    # 채팅 히스토리 요약 시스템 프롬프트
    # ChatPromptTemplate의 시스템 프롬프트로 주입 <- input 매개변수로 입력받은 텍스트는 Human Message로 넣어 완성
    # MessagesPlaceholder는 시스템에 적재된 채팅 히스토리를 받아주는 역할
    contextualize_q_system_prompt = '''Given a chat history and the latest user question \
    which might reference context in the chat history, formulate a standalone question \
    which can be understood without the chat history. Do NOT answer the question, \
    just reformulate it if needed and otherwise return it as is.'''
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ('system', contextualize_q_system_prompt),
            MessagesPlaceholder('history'),
            ('human', '{input}'),
        ]
    )
    # 질문-답변 시스템 프롬프트
    qa_system_prompt = '''You are an assistant for question-answering tasks. \
    Use the following pieces of retrieved context to answer the question. \
    If you don't know the answer, just say that you don't know. \
    Keep the answer perfect. please use imogi with the answer.
    대답은 한국어로 하고, 존댓말을 써줘.\

    {context}
    '''
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ('system', qa_system_prompt),
            MessagesPlaceholder('history'),
            ('human', '{input}'),
        ]
    )

    llm = ChatOpenAI(model=selected_model)
    
    # 대화 히스토리를 고려해서 문서 검색
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    # 검색된 문서로 답변 생성
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt) 
    # 검색과 생성을 연결하는 최종 체인
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    return rag_chain

# -----------------------------
# Streamlit UI
st.header('헌법 Q&A 챗봇 👩‍⚖️')

option = st.selectbox('Select GPT Model', ('gpt-4o-mini', 'gpt-3.5-turbo'))
rag_chain = initialize_components(option)
chat_history = StreamlitChatMessageHistory(key='chat_messages')

# 질문, 답변했던 history 
conversational_rag_chain = RunnableWithMessageHistory(
    rag_chain,
    lambda session_id: chat_history,
    input_messages_key='input',
    history_messages_key='history',
    output_messages_key='answer',

)
if 'messages' not in st.session_state:
    st.session_state['messages'] = [{'role':'assistant', 'content':'헌법에 대해 무엇이든 물어보세요!'}]

for msg in chat_history.messages:
    st.chat_message(msg.type).write(msg.content)

# 월러스 연산자(:=) -> 할당표현식 : st.chat_input('Your question') 의 결과를 prompt_message에 할당
if prompt_message := st.chat_input('Your question'): # 사용자가 입력한 내용이 있으면 
    st.chat_message('human').write(prompt_message) #prompt_message : 사용자가 입력한 내용
    with st.chat_message('ai'):
        with st.spinner('Thinking...'): # 로딩중 
            config = {'configurable':{'session_id':'any'}}
            response = conversational_rag_chain.invoke(
                {'input':prompt_message}, 
                config=config
            )
            answer = response['answer']
            st.write(answer) # answer 값 화면에 보여주게 하기위해
            with st.expander('참고 문서 확인'):
                for doc in response['context']: # 참고 문서 doc
                    st.markdown(doc.metadata['source'], help=doc.page_content) # 화면에 표시




