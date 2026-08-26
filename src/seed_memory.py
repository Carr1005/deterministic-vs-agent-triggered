# seed_memory.py — course fixture. Run once during setup (and by reset_memory.py).
# Writes a PREVIOUS SESSION into the database — including the almond allergy —
# before the learner ever runs the bot. Round 1 is built on that fact.
import json
import os
import sqlite3

from openai import OpenAI

client = OpenAI()
EMBED_MODEL = "text-embedding-3-small"
DB_PATH = os.getenv("SNACKBOT_DB", "memory.db")
THREAD_ID = "snackbot-demo"

# A conversation that already happened. The allergy is stated here in plain words.
CONVERSATION = [
    ("user", "Hi! Any snack ideas for this afternoon?"),
    ("assistant", "Happy to help — anything I should know before I suggest something?"),
    ("user", "Yes, important: I'm allergic to almonds. Severely. Please never suggest them."),
    ("assistant", "Understood. I'll avoid almonds and anything containing them."),
    ("user", "Thanks. I'm in Paris, so local pastries are a plus."),
]

# Snack and allergen facts the bot may consult.
KNOWLEDGE = [
    "Macarons are made with almond flour; every macaron contains almonds.",
    "Financiers are small cakes made largely of almond flour.",
    "Frangipane, the filling in galette des rois and pithiviers, is an almond cream.",
    "Croissants and pain au chocolat are butter, flour and yeast, and contain no almonds.",
    "Meringues are egg white and sugar, naturally almond-free.",
    "Madeleines are small butter sponge cakes; the classic recipe contains no almonds.",
    "A severe almond allergy can cause anaphylaxis. Strict avoidance is the only reliable prevention.",
]


def embed(text: str) -> list:
    return client.embeddings.create(model=EMBED_MODEL, input=text).data[0].embedding


conn = sqlite3.connect(DB_PATH)
for table in ("CONVERSATIONAL_MEMORY", "CONVERSATION_VECTORS", "SEMANTIC_MEMORY"):
    conn.execute(f"DROP TABLE IF EXISTS {table}")

conn.execute("""CREATE TABLE CONVERSATIONAL_MEMORY (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT NOT NULL,
                    role      TEXT NOT NULL,
                    content   TEXT NOT NULL,
                    ts        TEXT DEFAULT CURRENT_TIMESTAMP)""")
conn.execute("""CREATE TABLE CONVERSATION_VECTORS (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    content   TEXT NOT NULL,
                    embedding TEXT NOT NULL)""")
conn.execute("""CREATE TABLE SEMANTIC_MEMORY (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    content   TEXT NOT NULL,
                    embedding TEXT NOT NULL)""")
conn.commit()
print(f"created 3 tables in {DB_PATH}")

# 1. the prior session, as exact rows (what a deterministic read will find)
conn.executemany(
    "INSERT INTO CONVERSATIONAL_MEMORY (thread_id, role, content) VALUES (?, ?, ?)",
    [(THREAD_ID, role, content) for role, content in CONVERSATION])
conn.commit()
print(f"seeded {len(CONVERSATION)} conversation turns")

# 2. the same session, embedded (what a semantic search will find)
print("embedding… (a few seconds)")
conn.executemany(
    "INSERT INTO CONVERSATION_VECTORS (content, embedding) VALUES (?, ?)",
    [(f"{role}: {content}", json.dumps(embed(content)))
     for role, content in CONVERSATION])

# 3. the snack/allergen knowledge base, embedded
conn.executemany(
    "INSERT INTO SEMANTIC_MEMORY (content, embedding) VALUES (?, ?)",
    [(fact, json.dumps(embed(fact))) for fact in KNOWLEDGE])
conn.commit()
print(f"embedded {len(CONVERSATION)} turns + {len(KNOWLEDGE)} knowledge-base facts")
print("\nThe allergy is now in the database, in two forms: an exact row and a vector.")
