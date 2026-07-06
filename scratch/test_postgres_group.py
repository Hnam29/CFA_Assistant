import os
from dotenv import load_dotenv
load_dotenv()

from database.db import get_bank_questions, init_db

print("Checking database engine...")
print("Is Postgres?", os.getenv("SUPABASE_DB_URL") is not None)

try:
    print("Testing get_bank_questions...")
    qs = get_bank_questions(topic="Ethical and Professional Standards", limit=2)
    print("Success! Retrieved:", len(qs))
except Exception as e:
    import traceback
    print("Error:")
    traceback.print_exc()
