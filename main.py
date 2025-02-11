import claude
import streamlit as st
import re

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
        st.info("Loading...")
    
    response = claude.get_question()
    extract_question(response)
    loading = False

    st.text(question)
    file = st.text_area(f"File: {filename}")
    file = base_code