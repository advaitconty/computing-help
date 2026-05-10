import pickle
import os
import requests
from importlib import import_module
from pathlib import Path


answer = ""
pickle_file = Path("data.pkl")


def get_streamlit_secrets():
    try:
        import streamlit as st

        return st.secrets
    except Exception:
        return {}


def get_confidential_module():
    try:
        return import_module("confidential")
    except ModuleNotFoundError:
        return None


def get_secret(name, default=None, section="openai"):
    env_value = os.getenv(name)
    if env_value:
        return env_value

    secrets = get_streamlit_secrets()
    try:
        if name in secrets:
            return secrets[name]

        section_values = secrets.get(section, {})
        if name in section_values:
            return section_values[name]
    except Exception:
        pass

    confidential = get_confidential_module()
    return getattr(confidential, name, default) if confidential else default


api_key = get_secret("OPENAI_API_KEY", "")
model = get_secret("OPENAI_MODEL", "gpt-4o-mini")
endpoint = get_secret("OPENAPI_ENDPOINT")
endpoint = get_secret("OPENAI_ENDPOINT", endpoint)

if endpoint is None:
    base_url = get_secret("OPENAI_BASE_URL", "https://api.openai.com/v1")
    endpoint = f"{base_url.rstrip('/')}/chat/completions"

messages = []


def get_base_prompt():
    with open("base-prompt.txt", "r") as file:
        return file.read()


def call_endpoint():
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    response = requests.post(
        endpoint,
        headers=headers,
        json={
            "model": model,
            "messages": messages,
            "max_tokens": 8192,
            "temperature": 1,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def humanify(response):
    global messages, answer

    choices = response.get("choices", [])
    if not choices:
        raise ValueError("Endpoint response did not include any choices.")

    answer = choices[0].get("message", {}).get("content", "")
    if not answer:
        raise ValueError("Endpoint response did not include assistant text.")

    messages.append({"role": "assistant", "content": answer})

    with open(pickle_file, "wb") as f:
        pickle.dump(messages, f)

    return answer


def j1_only_mode_from_topics(include_j2_topics):
    return "false" if include_j2_topics else "true"


def get_question(include_j2_topics=False):
    global messages

    j1_only_mode = j1_only_mode_from_topics(include_j2_topics)
    mode_parameter = f"J1_ONLY_MODE = {j1_only_mode}"

    messages = [{"role": "user", "content": f"{get_base_prompt()}\n\n{mode_parameter}"}]
    return humanify(call_endpoint())


def follow_up(type, user_prompt, include_j2_topics=False):
    global messages

    with open(pickle_file, "rb") as f:
        messages = pickle.load(f)

    j1_only_mode = j1_only_mode_from_topics(include_j2_topics)
    modded_input = f"<type>{type}</type>\n<user>\n{user_prompt}\n</user>\n<mode>\n{j1_only_mode}\n</mode>"
    messages.append({"role": "user", "content": modded_input})

    return humanify(call_endpoint())


def check_answers(file, include_j2_topics=False):
    global messages

    j1_only_mode = j1_only_mode_from_topics(include_j2_topics)
    modded_input = f"<type>check</type>\n<user>Please check this user's file:\n<file>\n{file}\n</file>\n</user>\n<mode>\n{j1_only_mode}\n</mode>"
    messages.append({"role": "user", "content": modded_input})

    return humanify(call_endpoint())


if __name__ == "__main__":
    message = get_question()
    print(message)
    print(follow_up("help", input(": ")))
