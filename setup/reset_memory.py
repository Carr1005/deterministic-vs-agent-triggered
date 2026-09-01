# reset_memory.py — fixture. Restores the clean "session 1" state by copying the
# shipped seed database over memory.db. Costs nothing and calls no API.
# Use it before Round 5's measured runs: deterministic writes accumulate turns, and an
# accumulating preload contaminates the very trial you are about to run. Memory systems
# contaminate their own measurements.
import os
import shutil

DB_PATH = os.getenv("SNACKBOT_DB", "memory.db")
HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "fixtures", "memory-seed.db")

if not os.path.exists(FIXTURE):
    raise SystemExit(
        f"the shipped seed database is missing: {FIXTURE}\n"
        "Regenerate it (author only, needs an API key):\n"
        "  SNACKBOT_DB=setup/fixtures/memory-seed.db .venv/bin/python src/seed_memory.py")

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"deleted {DB_PATH}")
else:
    print(f"{DB_PATH} was not there — nothing to delete")

shutil.copy(FIXTURE, DB_PATH)
print(f"restored {DB_PATH} from the shipped seed (5 turns + 12 vectors, no API calls)")
print("\nmemory reset to the clean session-1 state.")
