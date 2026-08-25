# snackbot.py — SnackBot. Round-0 baseline: the bare LLM call. No memory.
from openai import OpenAI

client = OpenAI()
MODEL = "gpt-5-mini"

SYSTEM_PROMPT = "You are SnackBot, a snack-recommendation assistant."


def call_llm(messages):
    response = client.chat.completions.create(model=MODEL, messages=messages)
    return response.choices[0].message


def run_turn(user_msg: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]
    return call_llm(messages).content


if __name__ == "__main__":
    QUESTION = "I'm in Paris — suggest a quick sweet snack for me."
    print(f"you → {QUESTION}")
    print(f"bot ← {run_turn(QUESTION)}")
