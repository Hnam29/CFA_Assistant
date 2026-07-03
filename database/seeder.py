import os
import logging
from pathlib import Path
from database.db import seed_question_bank, get_bank_stats

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.parent

def find_excel_file() -> Path | None:
    """Find any Excel question bank file in the root directory."""
    # Try the exact original name first
    exact_path = ROOT_DIR / "CFA_Question_Bank_720Q.xlsx"
    if exact_path.exists():
        return exact_path
        
    # Otherwise, search for any .xlsx file starting with "CFA_Question_Bank"
    for p in ROOT_DIR.glob("CFA_Question_Bank*.xlsx"):
        return p
        
    # Fallback: search for any .xlsx file at all in the root directory
    for p in ROOT_DIR.glob("*.xlsx"):
        if not p.name.startswith("~$"):  # Ignore Excel temp files
            return p
            
    return None

def auto_seed_default_bank() -> None:
    """
    Auto-seed the CFA question bank Excel file if it has changed or has not been seeded yet.
    """
    excel_path = find_excel_file()
    if not excel_path:
        logger.warning("No question bank Excel (.xlsx) file found in the root directory. Skipping auto-seed.")
        return

    xlsx_path = str(excel_path)
    state_file = ROOT_DIR / "database" / ".last_seeded.txt"
    
    # Get current file info
    try:
        mtime = os.path.getmtime(xlsx_path)
        size = os.path.getsize(xlsx_path)
        current_state = f"{excel_path.name}|{mtime}|{size}"
    except Exception:
        current_state = ""

    # Check last seeded state
    last_state = ""
    if state_file.exists():
        try:
            last_state = state_file.read_text().strip()
        except Exception:
            pass

    # If state has changed (or state file doesn't exist), run seeder!
    if current_state != last_state:
        logger.info(f"Detected new or modified Excel question bank: {excel_path.name}. Seeding questions...")
        try:
            inserted, skipped = seed_question_bank(xlsx_path)
            logger.info(f"Seeding completed. Inserted: {inserted}, Skipped/Duplicate: {skipped}.")
            
            # Save the new state so we don't re-seed on every reload
            state_file.write_text(current_state)
        except Exception as e:
            logger.exception(f"Error seeding question bank: {e}")
    else:
        logger.info(f"Excel question bank '{excel_path.name}' has not changed since last seed. Skipping.")
