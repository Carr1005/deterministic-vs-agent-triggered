# show_memory.py — fixture. Prints what memory holds, so the learner can SEE that
# the allergy is already stored before the bot ever runs (Round 1 demo).
import os
import sqlite3

DB_PATH = os.getenv("SNACKBOT_DB", "memory.db")
if not os.path.exists(DB_PATH):
    raise SystemExit(f"{DB_PATH} does not exist — run: bash setup/bootstrap.sh")

conn = sqlite3.connect(DB_PATH)
rows = conn.execute(
    "SELECT thread_id, role, content FROM CONVERSATIONAL_MEMORY ORDER BY id").fetchall()
for thread_id, role, content in rows:
    print(f"[{thread_id}] {role}: {content}")
print(f"\n{len(rows)} row(s) in CONVERSATIONAL_MEMORY")

n = conn.execute("SELECT COUNT(*) FROM CONVERSATION_VECTORS").fetchone()[0]
print(f"{n} embedded row(s) in CONVERSATION_VECTORS")

# The knowledge base is printed in full, not counted: Round 1's demo needs the learner to
# SEE which pastries carry almonds before the bot recommends one. The danger is invisible
# in the name — "macaron" says nothing about almond flour — so a row count would hide the
# very fact that makes the failure a failure.
print("\nSEMANTIC_MEMORY (the knowledge base):")
for (content,) in conn.execute("SELECT content FROM SEMANTIC_MEMORY ORDER BY id"):
    print(f"  · {content}")
print(f"\nfile: {DB_PATH} ({os.path.getsize(DB_PATH) / 1024:.0f} KB on disk)")
