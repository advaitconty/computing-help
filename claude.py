import anthropic
import confidential
import pickle

answer = ""

pickle_file = "data.pkl"

client = anthropic.Anthropic(
    api_key=confidential.ANTHROPIC_API_KEY,
)

with open("base-prompt.txt", "r") as file:
    prompt = file.read()

messages = []

def humanify(response):
    global messages, answer
    for block in response.content:
        if isinstance(block, anthropic.types.TextBlock):
            answer = block.text

    messages.append({"role": "assistant", "content": [{"type": "text", "text": answer}]})
    
    with open(pickle_file, "wb") as f:
        pickle.dump(messages, f)

    return answer

def get_question():
    global client, prompt, messages

    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=8192,
        temperature=1,
        messages=messages
    )

    print(message.content)

    return humanify(message)

def follow_up(type, user_prompt):
    global messages

    with open(pickle_file, "rb") as f:
        pickle.load(f)

    modded_input = f"<type>{type}</type>\n<user>\n{user_prompt}\n</user>"

    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": modded_input
                }
            ]
        }
    )

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=8192,
        temperature=1,
        messages=messages
    )

    return humanify(message)

def check_answers(file):
    global messages
    
    print(messages)

    modded_input = f"<type>check</type>\n<user>Please check this user's file:\n<file>\n{file}\n</file>\n</user>"

    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": modded_input
                }
            ]
        }
    )

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=8192,
        temperature=1,
        messages=messages
    )

    return humanify(message)


if __name__ == "__main__":
    message = get_question()
    print(message)
    print(follow_up("help", input(": ")))