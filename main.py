import claude
import streamlit as st
from streamlit_ace import st_ace
import re

if "loading" not in st.session_state:
    st.session_state.loading = False
    st.session_state.user_code = ""
    st.session_state.show_questions = False

def extract_question(text):
    global question, base_code, filename
    question_match = re.search(r"<question>(.*?)</question>", text, re.DOTALL)
    base_code_match = re.search(r"<base-code>(.*?)</base-code>", text, re.DOTALL)
    filename_match = re.search(r'<code-filename="(.*?)">', text)

    st.session_state.question = question_match.group(1).strip() if question_match else None
    st.session_state.base_code = base_code_match.group(1).strip() if base_code_match else None
    st.session_state.filename = filename_match.group(1).strip() if filename_match else None

def extract_checked_answers(text):
    response_match = re.search(r"<response>(.*?)</response>", text, re.DOTALL)
    score_match = re.search(r"<score>(.*?)</score>", text, re.DOTALL)

    st.session_state.response = response_match.group(1).strip() if response_match else None
    st.session_state.score = score_match.group(1).strip() if score_match else None
loading = False

st.title("Computing Helpbot")
st.write("Get some computing questions to solve")

questions = st.container()
show_questions = False

if st.button("Ask a question"):
    loading = True
    if loading:
        loading_info = st.info("Loading...")
    
    response = claude.get_question()
    extract_question(response)
    loading = False
    loading_info.empty()
    st.session_state.show_questions = True
    
if st.session_state.show_questions:
    with questions:
        st.text(st.session_state.question)
        st.text(f"File: {st.session_state.filename}")
        
        st.session_state.user_code = st_ace(
            value=st.session_state.base_code,
            language="python",
            theme="monokai",
            keybinding="vscode",
            font_size=14,
            tab_size=4,
            height=500
        )
        st.write("Please do not forgot to press 'Apply Changes' once you are done coding")

        if st.button("Submit answer"):
            loading = True
            if loading:
                st.info("Please wait as Claude checks your answers...")

            extract_checked_answers(claude.check_answers(st.session_state.user_code))

            st.write(f"{st.session_state.score}")
            st.write(f"Reason:\n{st.session_state.response}")
            loading = False
else:
    questions.empty()