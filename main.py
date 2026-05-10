import llm
import streamlit as st
from streamlit_ace import st_ace
import re
import ast
import subprocess
import sys
import tempfile
from pathlib import Path

EXECUTION_TIMEOUT_SECONDS = 5
DANGEROUS_IMPORTS = {
    "os",
    "subprocess",
    "shutil",
    "socket",
    "requests",
    "urllib",
    "pathlib",
    "pickle",
    "multiprocessing",
    "threading",
}
DANGEROUS_CALLS = {
    "eval",
    "exec",
    "compile",
    "__import__",
}

if "loading" not in st.session_state:
    st.session_state.loading = False
    st.session_state.user_code = ""
    st.session_state.show_questions = False
    st.session_state.include_j2_topics = False
    st.session_state.question_include_j2_topics = False
    st.session_state.question = None
    st.session_state.base_code = ""
    st.session_state.filename = "answer.py"
    st.session_state.response = None
    st.session_state.score = None
    st.session_state.execution_result = None

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

def validate_python_for_execution(code):
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        return False, f"Syntax error before execution: {error}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.split(".")[0]
                if module_name in DANGEROUS_IMPORTS:
                    return False, f"Execution blocked because importing `{module_name}` is not allowed."

        if isinstance(node, ast.ImportFrom):
            module_name = (node.module or "").split(".")[0]
            if module_name in DANGEROUS_IMPORTS:
                return False, f"Execution blocked because importing `{module_name}` is not allowed."

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in DANGEROUS_CALLS:
                return False, f"Execution blocked because `{node.func.id}()` is not allowed."

    return True, None

def run_user_code(code, filename, stdin_text):
    is_valid, validation_error = validate_python_for_execution(code)
    if not is_valid:
        return {
            "ok": False,
            "stdout": "",
            "stderr": validation_error,
            "returncode": None,
            "timed_out": False,
        }

    safe_filename = Path(filename or "answer.py").name
    if not safe_filename.endswith(".py"):
        safe_filename = "answer.py"

    with tempfile.TemporaryDirectory() as temp_dir:
        code_path = Path(temp_dir) / safe_filename
        code_path.write_text(code, encoding="utf-8")

        try:
            completed = subprocess.run(
                [sys.executable, "-I", str(code_path)],
                cwd=temp_dir,
                input=stdin_text,
                text=True,
                capture_output=True,
                timeout=EXECUTION_TIMEOUT_SECONDS,
                env={"PYTHONIOENCODING": "utf-8"},
            )
        except subprocess.TimeoutExpired as error:
            return {
                "ok": False,
                "stdout": error.stdout or "",
                "stderr": f"Execution stopped after {EXECUTION_TIMEOUT_SECONDS} seconds.",
                "returncode": None,
                "timed_out": True,
            }

    return {
        "ok": completed.returncode == 0,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
        "timed_out": False,
    }

st.title("Computing Helpbot")
st.caption("Practice H2 Computing Paper 2 questions with a code editor, checker, and local runner.")

toolbar_left, toolbar_right = st.columns([1, 2], vertical_alignment="bottom")
with toolbar_left:
    st.toggle("Include J2 topics", key="include_j2_topics")
with toolbar_right:
    ask_question = st.button("Ask a question", type="primary", use_container_width=True)

questions = st.container()
show_questions = False

if ask_question:
    loading = True
    if loading:
        loading_info = st.info("Loading...")
    
    st.session_state.question_include_j2_topics = st.session_state.include_j2_topics
    response = llm.get_question(st.session_state.question_include_j2_topics)
    extract_question(response)
    st.session_state.response = None
    st.session_state.score = None
    st.session_state.execution_result = None
    loading = False
    loading_info.empty()
    st.session_state.show_questions = True
    
if st.session_state.show_questions:
    with questions:
        question_panel, editor_panel = st.columns([1, 1.25], gap="large")

        with question_panel:
            st.subheader("Question")
            st.markdown(st.session_state.question or "_No question loaded._")
            st.caption(f"File: `{st.session_state.filename}`")

            if st.session_state.score or st.session_state.response:
                st.divider()
                st.subheader("Feedback")
                if st.session_state.score:
                    st.markdown(f"**Score:** {st.session_state.score}")
                if st.session_state.response:
                    st.markdown(st.session_state.response)

        with editor_panel:
            st.subheader("Answer")
            st.session_state.user_code = st_ace(
                value=st.session_state.base_code,
                language="python",
                theme="monokai",
                keybinding="vscode",
                font_size=14,
                tab_size=4,
                height=520,
                auto_update=True,
            )
            st.caption("The editor updates automatically as you type.")
            stdin_text = st.text_area(
                "Program input",
                placeholder="Optional stdin. Put each input() value on a new line.",
                height=90,
            )

            action_left, action_right = st.columns(2)
            with action_left:
                run_code = st.button("Run file", use_container_width=True)
            with action_right:
                submit_answer = st.button("Submit answer", type="primary", use_container_width=True)

            if run_code:
                st.session_state.execution_result = run_user_code(
                    st.session_state.user_code,
                    st.session_state.filename,
                    stdin_text,
                )

            if submit_answer:
                loading = True
                if loading:
                    st.info("Please wait while your answer is checked...")

                extract_checked_answers(llm.check_answers(st.session_state.user_code, st.session_state.question_include_j2_topics))
                loading = False

            if st.session_state.execution_result:
                result = st.session_state.execution_result
                st.divider()
                st.subheader("Run output")
                if result["ok"]:
                    st.success("File ran successfully.")
                else:
                    st.error("File did not complete successfully.")

                if result["stdout"]:
                    st.markdown("**stdout**")
                    st.code(result["stdout"], language="text")
                if result["stderr"]:
                    st.markdown("**stderr**")
                    st.code(result["stderr"], language="text")
                if result["returncode"] is not None:
                    st.caption(f"Exit code: {result['returncode']}")
else:
    questions.empty()
