# snackbot.py — after Round 4: the five-run harness (reads still all agent-triggered).
import json
import os
import sqlite3
import sys

from meter import report, timed
from openai import OpenAI

client = OpenAI()
MODEL = "gpt-5-mini"

SYSTEM_PROMPT = (
    "You are SnackBot, a snack-recommendation assistant. You have memory of past "
    "conversations with this user, and a knowledge base of snack and allergen facts. "
    "You may consult them if useful."
)


def call_llm(messages, tools=None):
    kwargs = {"model": MODEL, "messages": messages}
    if tools:
        kwargs["tools"] = tools
    response = client.chat.completions.create(**kwargs)
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


# ---- S3.1: agent-triggered reads — two TOOLS over the same database ---------
# S3.3: semantic search — matches by meaning, not keywords. An embedding is just
# a list of numbers; two texts that mean the same thing get nearby lists, so the
# comparison below finds "allergic to almonds" from a query about "dietary needs".
EMBED_MODEL = "text-embedding-3-small"


def embed(text: str) -> list:
    return client.embeddings.create(model=EMBED_MODEL, input=text).data[0].embedding


def cosine(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = (sum(x * x for x in a) ** 0.5) * (sum(y * y for y in b) ** 0.5)
    return dot / norm if norm else 0.0


def semantic_search(table: str, query: str, k: int = 3) -> str:
    """Rank every row in `table` by meaning-similarity to `query`."""
    q = embed(query)
    rows = conn.execute(f"SELECT content, embedding FROM {table}").fetchall()
    ranked = sorted(((cosine(q, json.loads(vec)), text) for text, vec in rows),
                    reverse=True)
    return "\n".join(text for _, text in ranked[:k]) or "(nothing found)"


def search_memory(query: str) -> str:
    """Search past conversations with this user."""
    print(f"[tool] search_memory({query!r})")
    return semantic_search("CONVERSATION_VECTORS", query)


def search_knowledge_base(query: str) -> str:
    """Search snack and allergen facts."""
    print(f"[tool] search_knowledge_base({query!r})")
    return semantic_search("SEMANTIC_MEMORY", query)


def _schema(name: str, description: str) -> dict:
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object",
                       "properties": {"query": {"type": "string"}},
                       "required": ["query"]}}}


TOOLS = [
    _schema("search_memory", "Search past conversations with this user."),
    _schema("search_knowledge_base", "Search snack and allergen facts."),
]
TOOL_FNS = {"search_memory": search_memory,
            "search_knowledge_base": search_knowledge_base}


def run_turn(user_msg: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]
    save_turn("user", user_msg)      # S3.2: writes stay deterministic
    total_ms = 0.0
    for _ in range(5):               # let the model call tools, then answer
        msg, ms = timed(call_llm, messages, TOOLS)
        total_ms += ms
        if not msg.tool_calls:
            break
        messages.append({
            "role": "assistant", "content": msg.content or "",
            "tool_calls": [{"id": tc.id, "type": "function",
                            "function": {"name": tc.function.name,
                                         "arguments": tc.function.arguments}}
                           for tc in msg.tool_calls]})
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": TOOL_FNS[tc.function.name](**args)})
    reply = msg.content or ""
    prompt_text = "\n".join(str(m.get("content") or "") for m in messages)
    save_turn("assistant", reply)    # S3.2: writes stay deterministic
    report(prompt_text, reply, total_ms)
    return reply


# S4.1: reliability by repetition — same turn ×5, count SAFE replies.
# S4.2: the signal is "allerg", not "macaron" — unsafe replies name the macaron too.
def run_n(n: int = 5, question: str = "I'm in Paris — suggest a quick sweet snack for me.",
          signal: str = "allerg") -> None:
    safe = 0
    for i in range(1, n + 1):
        reply = run_turn(question)
        ok = signal in reply.lower()
        safe += ok
        print(f"  run {i}: {'SAFE' if ok else 'UNSAFE'}")
    print(f"\n{safe}/{n} replies acknowledged the allergy")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--x5":   # S4.1: the five-run harness
        run_n(5)
    else:
        QUESTION = " ".join(args) or "I'm in Paris — suggest a quick sweet snack for me."
        print(f"you → {QUESTION}")
        print(f"bot ← {run_turn(QUESTION)}")
