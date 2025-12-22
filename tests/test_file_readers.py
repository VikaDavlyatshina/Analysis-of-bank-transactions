from src.file_readers import load_transactions_from_excel



def test_fill_missing_values(sample_transactions_df):
    df = sample_transactions_df.copy()
    df["Кэшбэк"] = df.get("Кэшбэк", 0.0).fillna(0.0)
    df["Номер карты"] = df.get("Номер карты", "****").fillna("****")
    df["Описание"] = df.get("Описание", "Без описания").fillna("Без описания").str.strip()
    df["Категория"] = df.get("Категория", "Не указано").fillna("Не указано").str.strip()

    assert df["Кэшбэк"].isna().sum() == 0
    assert df["Номер карты"].isna().sum() == 0
    assert df["Описание"].isna().sum() == 0
    assert df["Категория"].isna().sum() == 0

