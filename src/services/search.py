from pathlib import Path
from typing import Any, Dict, List, Optional

from config import setup_services_logger
from src.reports import report_to_file

logger = setup_services_logger()


@report_to_file
def simple_search(
    transactions: List[Dict[str, Any]],
    search_string: str,
    reports_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    if reports_dir:
        logger.debug(f"Директория для сохранения отчета: {reports_dir}")

    if not isinstance(search_string, str) or not search_string.strip():
        return {
            "service": "Простой поиск",
            "status": "success",
            "search_string": "",
            "found_count": 0,
            "transactions": [],
            "message": "Строка поиска пуста",
            "skip_save": True,
        }

    search_lower = search_string.lower()

    def contains_search_text(transaction: Dict[str, Any]) -> bool:
        if not isinstance(transaction, dict):
            return False
        desc = str(transaction.get("Описание", "")).lower()
        cat = str(transaction.get("Категория", "")).lower()
        return search_lower in desc or search_lower in cat

    result_transactions: List[Dict[str, Any]] = list(filter(contains_search_text, transactions))

    result = {
        "service": "Простой поиск",
        "status": "success",
        "search_string": search_string,
        "found_count": len(result_transactions),
        "transactions": result_transactions,
        "message": f"Найдено {len(result_transactions)} транзакций по запросу '{search_string}'",
    }

    return result
