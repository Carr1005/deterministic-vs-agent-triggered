# snackbot.py — after Round 2: deterministic memory (exact SQL read + write, every turn).
import os
import sqlite3
import sys

from meter import report, timed
from openai import OpenAI

client = OpenAI()
MODEL = "gpt-5.6-luna"

SYSTEM_PROMPT = "You are SnackBot, a snack-recommendation assistant."


def call_llm(messages):
    response = client.chat.completions.create(model=MODEL, messages=messages)
    return response.choices[0].message


# ---- the store: ONE SQLite file, used by every memory operation --------------
DB_PATH = os.getenv("SNACKBOT_DB", "memory.db")
THREAD_ID = "snackbot-demo"
conn = sqlite3.connect(DB_PATH)


def read_user_facts() -> str:
    """Exact SQL read of this thread's prior turns, oldest first."""
    rows = conn.execute(
        """SELECT role, content FROM CONVERSATIONAL_MEMORY
           WHERE thread_id = ? ORDER BY id""",
        (THREAD_ID,),
    ).fetchall()
    return "\n".join(f"{role}: {content}" for role, content in rows)


def save_turn(role: str, content: str) -> None:
    """Persist one turn. No judgment call, no exceptions."""
    conn.execute(
        """INSERT INTO CONVERSATIONAL_MEMORY (thread_id, role, content)
           VALUES (?, ?, ?)""",
        (THREAD_ID, role, content),
    )
    conn.commit()


def run_turn(user_msg: str) -> str:
    user_facts = read_user_facts()   # S2.1: deterministic read — runs no matter what
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",
         "content": f"What I know about this user:\n{user_facts}\n\nUser: {user_msg}"},
    ]
    prompt_text = "\n".join(m["content"] for m in messages)
    save_turn("user", user_msg)      # S2.2: deterministic write — runs no matter what
    reply_msg, ms = timed(call_llm, messages)
    reply = reply_msg.content
    save_turn("assistant", reply)    # S2.2: deterministic write — runs no matter what
    report(prompt_text, reply, ms)   # S1.2: meter every turn — tokens, cost, latency
    return reply


if __name__ == "__main__":
    QUESTION = " ".join(sys.argv[1:]) or "I'm in Paris — suggest a quick sweet snack for me."
    print(f"you → {QUESTION}")
    print(f"bot ← {run_turn(QUESTION)}")
