from typing import Any, Dict, List

import pandas as pd

from config import setup_views_logger

logger = setup_views_logger()


def get_cards_summary(df: pd.DataFrame) -> List[Dict[str, Any]]:
    logger.debug(f"Начало расчета статистики по картам. Всего транзакций: {len(df)}")

    if df.empty:
        logger.info("DataFrame пустой, возвращаем пустой список")
        return []

    expenses_df = df[df["Сумма операции"] < 0].copy()
    logger.debug(f"Найдено расходных операций: {len(expenses_df)}")

    if expenses_df.empty:
        logger.info("Нет расходных операций, возвращаем пустой список")
        return []

    result: List[Dict[str, Any]] = []

    for card_number, group in expenses_df.groupby("Номер карты"):
        total_spent = float(abs(group["Сумма операции"].sum()))
        cashback = total_spent * 0.01
        last_digits = str(card_number)[-4:] if card_number else ""

        logger.debug(f"Карта {last_digits}: расходы={total_spent:.2f}, кэшбэк={cashback:.2f}")

        result.append(
            {
                "last_digits": last_digits,
                "total_spent": round(total_spent, 2),
                "cashback": round(cashback, 2),
            }
        )

    result.sort(key=lambda x: x["total_spent"], reverse=True)
    logger.info(f"Рассчитана статистика по {len(result)} картам")

    return result
