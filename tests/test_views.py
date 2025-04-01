import json
from unittest.mock import patch

import pandas as pd
import pytest

from src.views import get_events

@pytest.mark.parametrize(
    "finish_date, range_date, expected", [
        ("25.01.2025", "W", {"expenses": {"total_amount": 2094,
                                          "main": [{"category": "Аптеки", "amount": 1794.0}],
                                          "transfers_and_cash": [{"category": "Переводы", "amount": 300.0}]},
                             "income": {"total_amount": 0, "main": []},
                             "currency_rates": [{"currency": "USD", "rate": 73.21},
                                                {"currency": "EUR", "rate": 87.08}],
                             "stock_prices": [{"stock": "AAPL", "price": 150.12},
                                              {"stock": "AMZN", "price": 3173.18}]}
        ),
        ("25.01.2025", "M", {"expenses": {"total_amount": 6956,
                                          "main": [{"category": "АЗС", "amount": 2500.0},
                                                   {"category": "Аптеки", "amount": 1794.0},
                                                   {"category": "Супермаркеты", "amount": 1162.0}],
                                          "transfers_and_cash": [{"category": "Наличные", "amount": 1200.0},
                                                                 {"category": "Переводы", "amount": 300.0}]},
                             "income": {"total_amount": 500, "main": [{"category": "Пополнения", "amount": 500.0}]},
                             "currency_rates": [{"currency": "USD", "rate": 73.21},
                                                {"currency": "EUR", "rate": 87.08}],
                             "stock_prices": [{"stock": "AAPL", "price": 150.12},
                                              {"stock": "AMZN", "price": 3173.18}]}
         ),
        ("07.02.2025", "Y", {"expenses": {"total_amount": 9229,
                                          "main": [{"category": "АЗС", "amount": 2500.0},
                                                   {"category": "Супермаркеты", "amount": 2085.0},
                                                   {"category": "Аптеки", "amount": 1794.0},
                                                   {"category": "Кафе", "amount": 1350.0}],
                                          "transfers_and_cash": [{"category": "Наличные", "amount": 1200.0},
                                                                 {"category": "Переводы", "amount": 300.0}]},
                             "income": {"total_amount": 500, "main": [{"category": "Пополнения", "amount": 500.0}]},
                             "currency_rates": [{"currency": "USD", "rate": 73.21},
                                                {"currency": "EUR", "rate": 87.08}],
                             "stock_prices": [{"stock": "AAPL", "price": 150.12},
                                              {"stock": "AMZN", "price": 3173.18}]}
)
    ]
)
def test_get_events(transactions, finish_date, range_date, expected):
    """
    Тест для проверки правильной работы функции get_events
    """
    return_get_currency_rates = [{"currency": "USD", "rate": 73.21},
                                 {"currency": "EUR", "rate": 87.08}]
    return_get_stocks_prices = [{"stock": "AAPL", "price": 150.12},
               {"stock": "AMZN", "price": 3173.18}]

    with patch("src.views.get_currency_rates", return_value=return_get_currency_rates) as mock_currency:
        with patch("src.views.get_stocks_prices", return_value=return_get_stocks_prices):
            result = get_events(transactions, finish_date, range_date)

    assert result == json.dumps(expected, ensure_ascii=False)
