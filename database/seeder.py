import os
import re
import logging
import hashlib
from pathlib import Path
from database.db import seed_question_bank, get_bank_stats

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.parent

def find_excel_file() -> Path | None:
    """Find any Excel question bank file in the root directory."""
    exact_path = ROOT_DIR / "CFA_Question_Bank_720Q.xlsx"
    if exact_path.exists():
        return exact_path
        
    for p in ROOT_DIR.glob("CFA_Question_Bank*.xlsx"):
        return p
        
    for p in ROOT_DIR.glob("*.xlsx"):
        if not p.name.startswith("~$"):  # Ignore Excel temp files
            return p
            
    return None

def download_google_sheet(sheet_url: str, output_path: Path) -> bool:
    """Download Google Sheet as an Excel file using its share link."""
    import requests
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_url)
    if not match:
        logger.error("Invalid Google Sheet URL format.")
        return False
        
    spreadsheet_id = match.group(1)
    export_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=xlsx"
    
    try:
        response = requests.get(export_url, timeout=15)
        if response.status_code == 200:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(response.content)
            return True
        else:
            logger.error(f"Failed to export Google Sheet. HTTP Status: {response.status_code}")
            return False
    except Exception as e:
        logger.exception(f"Error downloading Google Sheet: {e}")
        return False

def auto_seed_default_bank() -> None:
    """
    Auto-seed the CFA question bank Excel file if it has changed or has not been seeded yet.
    Supports local Excel file or a remote Google Sheets URL via GOOGLE_SHEET_URL env variable.
    """
    google_sheet_url = os.getenv("GOOGLE_SHEET_URL", "").strip()
    state_file = ROOT_DIR / "database" / ".last_seeded.txt"
    temp_xlsx_path = ROOT_DIR / "data" / "cfa_question_bank_temp.xlsx"
    
    using_google = False
    xlsx_path = ""
    current_state = ""

    if google_sheet_url:
        logger.info("GOOGLE_SHEET_URL found. Attempting to fetch latest questions from Google Sheets...")
        if download_google_sheet(google_sheet_url, temp_xlsx_path):
            using_google = True
            xlsx_path = str(temp_xlsx_path)
            # Compute hash of downloaded content to detect changes
            try:
                content = temp_xlsx_path.read_bytes()
                file_hash = hashlib.sha256(content).hexdigest()
                current_state = f"google|{file_hash}"
            except Exception:
                current_state = ""
        else:
            logger.warning("Failed to fetch Google Sheet. Falling back to local Excel scanning...")

    if not using_google:
        excel_path = find_excel_file()
        if not excel_path:
            logger.warning("No question bank Excel (.xlsx) file found. Skipping auto-seed.")
            return
        xlsx_path = str(excel_path)
        try:
            mtime = os.path.getmtime(xlsx_path)
            size = os.path.getsize(xlsx_path)
            current_state = f"local|{excel_path.name}|{mtime}|{size}"
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
        logger.info(f"Detected change in question source. Seeding questions from {xlsx_path}...")
        try:
            inserted, skipped = seed_question_bank(xlsx_path)
            logger.info(f"Seeding completed. Inserted: {inserted}, Skipped/Duplicate: {skipped}.")
            
            # Save the new state so we don't re-seed on every reload
            if current_state:
                state_file.write_text(current_state)
        except Exception as e:
            logger.exception(f"Error seeding question bank: {e}")
    else:
        logger.info("Question bank source has not changed since last seed. Skipping.")

