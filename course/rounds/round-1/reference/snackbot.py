# snackbot.py — after Round 1: metered (tokens / cost / latency on every turn).
from meter import report, timed
from openai import OpenAI

client = OpenAI()
MODEL = "gpt-5.6-luna"

SYSTEM_PROMPT = "You are SnackBot, a snack-recommendation assistant."


def call_llm(messages):
    response = client.chat.completions.create(model=MODEL, messages=messages)
    return response.choices[0].message


def run_turn(user_msg: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]
    prompt_text = "\n".join(m["content"] for m in messages)
    reply_msg, ms = timed(call_llm, messages)
    reply = reply_msg.content
    report(prompt_text, reply, ms)   # S1.2: meter every turn — tokens, cost, latency
    return reply


if __name__ == "__main__":
    QUESTION = "I'm walking down Rue Bonaparte in Saint-Germain — suggest a sweet to pick up nearby."
    print(f"you → {QUESTION}")
    print(f"bot ← {run_turn(QUESTION)}")
