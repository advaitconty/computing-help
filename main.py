import claude
import streamlit as st
from streamlit_ace import st_ace
import re

st.session_state.loading = False

def extract_question(text):
    global question, base_code, filename
    question_match = re.search(r"<question>(.*?)</question>", text, re.DOTALL)
    base_code_match = re.search(r"<base-code>(.*?)</base-code>", text, re.DOTALL)
    filename_match = re.search(r'<code-filename="(.*?)">', text)

    question = question_match.group(1).strip() if question_match else None
    base_code = base_code_match.group(1).strip() if base_code_match else None
    filename = filename_match.group(1).strip() if filename_match else None

loading = False

st.title("Computing Helpbot")
st.write("Welcome to Computing Helpbot!.")

if st.button("Ask a question"):
    loading = True
    if loading:
        loading_info = st.info("Loading...")
    
    response = claude.get_question()
    extract_question(response)
    loading = False
    loading_info.empty()

    st.text(question)
    st.text(f"File: {filename}")
    
    code = st_ace(
        value=base_code,
        language="python",
        theme="monokai",
        keybinding="vscode",
        font_size=14,
        tab_size=4,
        height=200
    )