from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
USER_SETTINGS = PROJECT_ROOT / "config" / "user_settings.json"
LOGS_DIR = PROJECT_ROOT / "logs"
REPORTS_DIR = PROJECT_ROOT / "reports"

EXCEL_FILE = DATA_DIR / "operations.xlsx"
