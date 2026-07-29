import json
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional

import pandas as pd

from config import REPORTS_DIR, setup_reports_logger

logger = setup_reports_logger()


def report_to_file(func: Optional[Callable[..., Any]] = None, *, filename: Optional[str] = None) -> Callable[..., Any]:
    def decorator(inner_func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(inner_func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = inner_func(*args, **kwargs)

                reports_dir = kwargs.get("reports_dir", REPORTS_DIR)
                reports_dir = Path(reports_dir)

                if isinstance(result, dict) and result.get("skip_save", False):
                    logger.debug(f"Пропускаем сохранение для {inner_func.__name__} (skip_save=True)")
                    return result

                if isinstance(result, pd.DataFrame) and result.empty:
                    logger.info(f"Отчет пустой - файл не сохраняется для {inner_func.__name__}")
                    return result

                if isinstance(result, dict):
                    if result.get("found_count", 0) == 0:
                        if result.get("total_phones_found", 0) == 0:
                            logger.info(f"Нет результатов для сохранения в {inner_func.__name__}")
                            return result

                    if "transactions" in result and len(result["transactions"]) == 0:
                        logger.info(f"Пустой список транзакций в {inner_func.__name__}")
                        return result

                if filename is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_name = f"{inner_func.__name__}_{timestamp}.json"
                else:
                    file_name = filename

                file_path = reports_dir / file_name
                reports_dir.mkdir(parents=True, exist_ok=True)

                try:
                    if isinstance(result, pd.DataFrame):
                        data = result.to_dict(orient="records")
                    else:
                        data = result

                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

                    logger.info(f"Отчет сохранен: {file_path}")

                    if isinstance(result, dict):
                        result = result.copy()
                        result["report_file"] = str(file_path)
                        result["report_filename"] = file_name

                except Exception as e:
                    logger.error(f"Ошибка сохранения отчёта {file_name}: {e}")
                return result

            except Exception as e:
                logger.error(f"Ошибка в декораторе report_to_file: {e}")
                raise

        return wrapper

    if func is not None:
        return decorator(func)

    return decorator
