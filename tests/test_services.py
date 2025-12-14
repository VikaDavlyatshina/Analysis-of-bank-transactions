import json
from src.services import investment_bank, simple_search, find_phone_numbers

# -----------------------------
# Тест для investment_bank
# -----------------------------
def test_investment_bank(tmp_path):
    transactions = [
        {"Дата операции": "2025-12-01", "Сумма операции": -95},
        {"Дата операции": "2025-12-01", "Сумма операции": -120},
        {"Дата операции": "2025-11-30", "Сумма операции": -50},
    ]
    month = "2025-12"
    limit = 100

    total = investment_bank(month, transactions, limit, reports_dir=tmp_path)

    # Проверяем, что сумма корректного типа
    assert isinstance(total, float)

    # Проверяем создание отчета
    report_file = tmp_path / "investment_bank_report.json"
    assert report_file.exists()

    data = json.loads(report_file.read_text(encoding="utf-8"))
    assert data["month"] == month
    assert data["total_investment"] == total

# -----------------------------
# Тест для simple_search
# -----------------------------
def test_simple_search(tmp_path):
    transactions = [
        {"Описание": "Оплата ЖКХ", "Категория": "Коммунальные услуги"},
        {"Описание": "Перевод другу", "Категория": "Переводы"},
        {"Описание": "Покупка в магазине", "Категория": "Питание"},
    ]
    search_string = "перевод"

    result = simple_search(transactions, search_string, reports_dir=tmp_path)

    # Проверяем корректность поиска
    assert result["found_count"] == 1
    assert result["transactions"][0]["Описание"] == "Перевод другу"

    # Проверяем сохранение отчета
    report_file = tmp_path / "simple_search_report.json"
    assert report_file.exists()
    saved = json.loads(report_file.read_text(encoding="utf-8"))
    assert saved["found_count"] == 1

# -----------------------------
# Тест для find_phone_numbers
# -----------------------------
def test_find_phone_numbers(tmp_path):
    transactions = [
        {"Описание": "Оплата +7 912 345-67-89"},
        {"Описание": "Перевод другу"},
        {"Описание": "Встреча с клиентом 89123456789"},
    ]

    result = find_phone_numbers(transactions, reports_dir=tmp_path)

    # Проверяем количество найденных транзакций с телефонами
    assert result["found_count"] == 2

    # Проверяем сохранение отчета
    report_file = tmp_path / "find_phone_numbers_report.json"
    assert report_file.exists()
    saved = json.loads(report_file.read_text(encoding="utf-8"))
    assert saved["found_count"] == 2

def test_investment_bank_empty_month(tmp_path):
    # Нет транзакций для данного месяца
    transactions = [
        {"Дата операции": "2025-11-30", "Сумма операции": -50},
        {"Дата операции": "2025-11-15", "Сумма операции": -30},
    ]
    month = "2025-12"
    limit = 100

    total = investment_bank(month, transactions, limit, reports_dir=tmp_path)
    assert total == 0.0

    report_file = tmp_path / "investment_bank_report.json"
    assert report_file.exists()
    data = json.loads(report_file.read_text(encoding="utf-8"))
    assert data["total_investment"] == 0.0

# -----------------------------
# Тест для simple_search с пустой строкой
# -----------------------------
def test_simple_search_empty_string(tmp_path):
    transactions = [
        {"Описание": "Оплата ЖКХ", "Категория": "Коммунальные услуги"},
        {"Описание": "Перевод другу", "Категория": "Переводы"},
    ]
    search_string = ""

    result = simple_search(transactions, search_string, reports_dir=tmp_path)
    assert result["status"] == "empty"
    assert result["found_count"] == 0
    assert result["transactions"] == []

    report_file = tmp_path / "simple_search_report.json"
    assert not report_file.exists()  # Отчёт не создаётся при пустом поиске

# -----------------------------
# Тест для find_phone_numbers с пустым списком
# -----------------------------
def test_find_phone_numbers_empty(tmp_path):
    transactions = []

    result = find_phone_numbers(transactions, reports_dir=tmp_path)
    assert result["status"] == "empty"
    assert result["found_count"] == 0
    assert result["transactions"] == []

    report_file = tmp_path / "find_phone_numbers_report.json"
    assert not report_file.exists()  # Отчёт не создаётся при пустом списке

# -----------------------------
# Тест для find_phone_numbers без номеров
# -----------------------------
def test_find_phone_numbers_no_numbers(tmp_path):
    transactions = [
        {"Описание": "Оплата продуктов"},
        {"Описание": "Перевод другу"},
    ]

    result = find_phone_numbers(transactions, reports_dir=tmp_path)
    assert result["status"] == "success"
    assert result["found_count"] == 0
    assert result["transactions"] == []

    report_file = tmp_path / "find_phone_numbers_report.json"
    assert report_file.exists()
    saved = json.loads(report_file.read_text(encoding="utf-8"))
    assert saved["found_count"] == 0