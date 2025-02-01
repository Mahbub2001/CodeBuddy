import os
import re
from PIL import Image
import sqlite3
import base64
import streamlit as st
from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename
from langchain.text_splitter import CharacterTextSplitter
from langchain.llms import Ollama
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import LLMChain, ConversationalRetrievalChain
from templates import css, bot_template, user_template
from code_editor import code_editor_view
from database import create_messages_db, write_to_messages_db, get_all_thread_messages, \
    get_unique_thread_ids
from prompts import CHAT_TEMPLATE, INITIAL_TEMPLATE
from prompts import CORRECTION_CONTEXT, COMPLETION_CONTEXT, OPTIMIZATION_CONTEXT, GENERAL_ASSISTANT_CONTEXT, \
    GENERATION_CONTEXT, COMMENTING_CONTEXT, EXPLANATION_CONTEXT, LEETCODE_CONTEXT, SHORTENING_CONTEXT

def config():
    st.set_page_config(
        page_title="CodeBuddy",
        page_icon="🤖",
        layout="centered",
        initial_sidebar_state="expanded"
    )
    st.markdown(css, unsafe_allow_html=True)


def init_ses_states():
    default_values = {
        'chat_history': [],
        'initial_input': "",
        'initial_context': "",
        'scenario_context': "",
        'thread_id': "",
        'docs_processed': False,
        'docs_chain': None,
        'user_authenticated': False,
        'uploaded_docs': None,
        'current_user_id': None
    }
    for key, value in default_values.items():
        st.session_state.setdefault(key, value)


def page_title_header():
    top_image = Image.open('logo.png')
    with open('logo.png', "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
        <div style="text-align: center;">
            <img src="data:image/png;base64,{encoded_image}" alt="logo" style="width: 200px; margin-bottom: 10px;">
        </div>
        """,
        unsafe_allow_html=True
    )

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks


def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore


def create_retrieval_chain(vectorstore):
    llm = Ollama(model="llama3.1:latest", temperature=temperature)
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return conversation_chain


def create_llm_chain(prompt_template):
    memory = ConversationBufferMemory(input_key="input", memory_key="chat_history")
    llm = Ollama(model="llama3.1:latest", temperature=temperature)
    return LLMChain(llm=llm, prompt=prompt_template, memory=memory)

def sidebar():
    global language, scenario, temperature, model, scenario_context, libraries, pdf_docs, uploaded_docs
    languages = sorted(['Python', 'GoLang', 'TypeScript', 'JavaScript', 'Java', 'C', 'C++', 'C#', 'R', 'SQL'])
    python_libs = sorted(['SQLite', 'PyGame', 'Seaborn', "Pandas", 'Numpy', 'Scipy', 'Scikit-Learn', 'PyTorch',
                          'TensorFlow', 'Streamlit', 'Flask', 'FastAPI'])
    scenarios = ['General Assistant', 'Code Correction', 'Code Completion', 'Code Commenting', 'Code Optimization',
                 'Code Shortener', 'Code Generation', 'Code Explanation', 'LeetCode Solver']
    scenario_context_map = {
        "Code Correction": CORRECTION_CONTEXT,
        "Code Completion": COMPLETION_CONTEXT,
        "Code Optimization": OPTIMIZATION_CONTEXT,
        "General Assistant": GENERAL_ASSISTANT_CONTEXT,
        "Code Generation": GENERATION_CONTEXT,
        "Code Commenting": COMMENTING_CONTEXT,
        "Code Explanation": EXPLANATION_CONTEXT,
        "LeetCode Solver": LEETCODE_CONTEXT,
        "Code Shortener": SHORTENING_CONTEXT,
    }

    with st.sidebar:
        if st.session_state:
            with st.expander(label="Settings", expanded=True):
                coding_settings_tab, chatbot_settings_tab = st.tabs(['Coding', 'ChatBot'])
                with coding_settings_tab:
                    language = st.selectbox(label="Language", options=languages)
                    if language == "Python":
                        libraries = st.multiselect(label="Libraries", options=python_libs)
                        if not libraries:
                            libraries = ""
                    else:
                        libraries = ""
                    scenario = st.selectbox(label="Scenario", options=scenarios, index=0)
                    scenario_context = scenario_context_map.get(scenario, "")

                with chatbot_settings_tab:
                    temperature = st.slider(label="Temperature", min_value=0.0, max_value=1.0, value=0.5)

            with st.expander(label="Embed Documents", expanded=True):
                pdf_docs = st.file_uploader("Upload Docs Here", type=['PDF'], accept_multiple_files=True)
                if pdf_docs:
                    if st.button("Process Docs"):
                        st.session_state.uploaded_docs = pdf_docs
                        raw_text = get_pdf_text(pdf_docs)
                        text_chunks = get_text_chunks(raw_text)
                        vectorstore = get_vectorstore(text_chunks)
                        initial_llm_chain = create_retrieval_chain(vectorstore=vectorstore)
                        st.session_state.docs_chain = initial_llm_chain
                        st.session_state.docs_processed = True
                else:
                    st.session_state.docs_processed = False
                if st.session_state.docs_processed:
                    st.write("Docs Successfully Processed:")
                    for i, pdf in enumerate(st.session_state.uploaded_docs):
                        st.caption(f"{i + 1}. {str(secure_filename(pdf.name))}")

            with st.expander("Previous Chats", expanded=True):
                selected_thread_id = st.selectbox(label="Previous Thread IDs", options=get_unique_thread_ids(), index=0)
                if st.button("Render Chat"):
                    st.session_state.thread_id = selected_thread_id
                    st.session_state.chat_history = get_all_thread_messages(selected_thread_id)
                    st.experimental_rerun()

        else:
            st.write("Login for additional features")


def display_history():
    with st.container():
        for i, message in enumerate(reversed(st.session_state.chat_history)):
            if i % 2 == 0:
                st.markdown(bot_template.replace("{{MSG}}", message), unsafe_allow_html=True)
            else:
                st.markdown(user_template.replace("{{MSG}}", message), unsafe_allow_html=True)


def user_initial_submit():
    global code_input, code_context
    initial_template = PromptTemplate(
        input_variables=['input', 'language', 'scenario', 'scenario_context', 'code_context', 'libraries'],
        template=INITIAL_TEMPLATE
    )
    if pdf_docs and st.session_state.docs_processed:
        initial_llm_chain = st.session_state.docs_chain
    else:
        initial_llm_chain = create_llm_chain(prompt_template=initial_template)
    code_input = st.text_area(label="User Code", height=200)
    code_context = st.text_area(label="Additional Context", height=100)
    if st.button("Submit Initial Input") and (code_input or code_context):
        with st.spinner('Generating Response...'):
            if st.session_state.docs_processed:
                llm_input = initial_template.format(
                    input=code_input,
                    code_context=code_context,
                    language=language,
                    scenario=scenario,
                    scenario_context=scenario_context,
                    libraries=libraries
                )
                initial_response = initial_llm_chain({'question': llm_input})['answer']
            else:
                initial_response = initial_llm_chain.run(
                    input=code_input,
                    code_context=code_context,
                    language=language,
                    scenario=scenario,
                    scenario_context=scenario_context,
                    libraries=libraries
                )
        st.session_state.update({
            'initial_input': code_input,
            'initial_context': code_context,
            'chat_history': [
                f"USER: CODE CONTEXT: {code_context} CODE INPUT: {code_input}",
                f"AI: {initial_response}"
            ],
        })
        st.session_state.thread_id = (code_context + code_input)[:40]
        write_to_messages_db(
            thread_id=st.session_state.thread_id,
            role='USER',
            message=f"USER: CODE CONTEXT: {code_context} CODE INPUT: {code_input}"
        )
        write_to_messages_db(
            thread_id=st.session_state.thread_id,
            role='AI',
            message=f"AI: {initial_response}"
        )


def user_message():
    chat_template = PromptTemplate(
        input_variables=[
            'input', 'language', 'scenario', 'scenario_context', 
            'chat_history', 'libraries', 'code_input', 
            'code_context', 'most_recent_ai_message'
        ],
        template=CHAT_TEMPLATE
    )
    if st.session_state.docs_processed:
        chat_llm_chain = st.session_state.docs_chain
    else:
        chat_llm_chain = create_llm_chain(prompt_template=chat_template)
    if st.session_state.chat_history:
        user_message = st.text_area("Further Questions for Coding AI?", key="user_input", height=100)
        if st.button("Submit Message") and user_message:
            with st.spinner('Generating Response...'):
                most_recent_ai_message = st.session_state.chat_history[-1]
                if st.session_state.docs_processed:
                    chat_input = chat_template.format(
                        input=user_message,
                        language=language,
                        scenario=scenario,
                        scenario_context=scenario_context,
                        libraries=libraries,
                        code_input=st.session_state.initial_input,
                        code_context=st.session_state.initial_context,
                        most_recent_ai_message=most_recent_ai_message
                    )
                    chat_response = chat_llm_chain({'question': chat_input})['answer']
                else:
                    chat_response = chat_llm_chain.run(
                        input=user_message,
                        language=language,
                        scenario=scenario,
                        scenario_context=scenario_context,
                        chat_history=st.session_state.chat_history,
                        libraries=libraries,
                        code_input=st.session_state.initial_input,
                        code_context=st.session_state.initial_context,
                        most_recent_ai_message=most_recent_ai_message
                    )
                st.session_state['chat_history'].append(f"USER: {user_message}")
                st.session_state['chat_history'].append(f"AI: {chat_response}")
                write_to_messages_db(
                    thread_id=st.session_state.thread_id,
                    role='USER',
                    message=f"USER: {user_message}"
                )
                write_to_messages_db(
                    thread_id=st.session_state.thread_id,
                    role='AI',
                    message=f"AI: {chat_response}"
                )

def display_file_code(filename):
    with open(filename, "r") as file:
        with st.expander(filename, expanded=False):
            st.code(file.read(), language='python')

def display_history():
    st.header("Chat History")
    for message in st.session_state.get('chat_history', []):
        if message.startswith("USER:"):
            st.markdown(f"**{message}**")
        elif message.startswith("AI:"):
            st.markdown(f"_{message}_")

def reduce_sidebar_width():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            min-width: 200px !important;
        }
        .block-container {
            max-width: 100% !important;  /* Ensure main content expands */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def main():
    config()
    reduce_sidebar_width() 
    create_messages_db()
    init_ses_states()
    sidebar()

    if "docs_processed" in st.session_state and st.session_state.docs_processed:
        code_editor, deploy_tab, docs_tab = st.tabs(['Code Editor', 'Chat Here', 'Doc Analysis'])
    else:
        code_editor, deploy_tab = st.tabs(['Code Editor', 'Chat Here'])
        docs_tab = None  

    with deploy_tab:
        st.container()  
        page_title_header()
        user_initial_submit()
        user_message()
        display_history()

    if docs_tab:
        with docs_tab:
            st.caption("Coming Soon")
            if st.session_state.uploaded_docs:
                for pdf in st.session_state.uploaded_docs:
                    st.caption(pdf.name)
            else:
                st.write("No documents uploaded yet.")

    with code_editor:
        code_editor_view()

if __name__ == "__main__":
    main()
