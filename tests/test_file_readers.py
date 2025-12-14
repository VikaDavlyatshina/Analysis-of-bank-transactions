import pandas as pd
from src.file_readers import load_transactions_from_excel

def test_load_transactions_from_excel(tmp_path):
    file = tmp_path / "test.xlsx"

    df = pd.DataFrame({
        "Дата операции": ["01.08.2021 12:00:00"],
        "Сумма операции": [-100],
        "Валюта операции": ["RUB"],
        "Категория": ["Еда"],
        "Описание": ["Кофе"],
        "Номер карты": ["1234"],
        "Статус": ["OK"]
    })

    df.to_excel(file, index=False)

    result = load_transactions_from_excel(file)

    assert len(result) == 1
    assert result["Дата операции"].dtype.name.startswith("datetime")