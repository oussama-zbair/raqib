from datetime import date

from app.scrapers.dates import parse_date, parse_int


def test_parse_date_arabic_and_french():
    assert parse_date("28 دجنبر 2026") == date(2026, 12, 28)
    assert parse_date("12 نونبر 2026") == date(2026, 11, 12)
    assert parse_date("5 شتنبر 2026") == date(2026, 9, 5)
    assert parse_date("15 Décembre 2026 \n - 16:30") == date(2026, 12, 15)
    assert parse_date("2 Février 2027") == date(2027, 2, 2)
    assert parse_date("غير محدد") is None
    assert parse_date(None) is None


def test_parse_int():
    assert parse_int("38 postes") == 38
    assert parse_int("٣ مناصب") == 3
    assert parse_int("sans chiffre") is None
