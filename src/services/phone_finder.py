import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import setup_services_logger
from src.reports import report_to_file

logger = setup_services_logger()


@report_to_file(filename="find_phone_numbers_report.json")
def find_phone_numbers(transactions: List[Dict[str, Any]], reports_dir: Optional[Path] = None) -> Dict[str, Any]:
    if reports_dir:
        logger.debug(f"Директория для сохранения отчета телефонов: {reports_dir}")

    logger.info(f"Поиск телефонов: всего транзакций={len(transactions)}")

    phone_pattern = re.compile(r"(?:\+7|7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{2,3}[\s\-]?\d{2}[\s\-]?\d{2}", re.IGNORECASE)

    found_transactions = []
    total_phones_found = 0

    for t in transactions:
        if not isinstance(t, dict):
            continue

        desc = str(t.get("Описание", ""))
        matches = phone_pattern.findall(desc)

        if matches:
            total_phones_found += len(matches)
            logger.debug(f"Найдены номера: '{desc}' → {matches}")

            t_copy = t.copy()
            t_copy["Найденные_телефоны"] = matches
            t_copy["Количество_найденных_номеров"] = len(matches)

            found_transactions.append(t_copy)

    result = {
        "service": "Поиск по телефонным номерам",
        "status": "success",
        "found_count": len(found_transactions),
        "found_transactions_count": len(found_transactions),
        "total_phones_found": total_phones_found,
        "transactions": found_transactions,
        "message": f"Найдено {len(found_transactions)} транзакций с {total_phones_found} телефонными номерами",
    }

    return result
