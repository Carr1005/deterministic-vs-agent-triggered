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

for table in ("CONVERSATION_VECTORS", "SEMANTIC_MEMORY"):
    n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{n} embedded row(s) in {table}")
print(f"\nfile: {DB_PATH} ({os.path.getsize(DB_PATH) / 1024:.0f} KB on disk)")
