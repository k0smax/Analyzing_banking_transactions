import datetime
import json
from unittest.mock import Mock

import pytest

from src.reports import spending_by_weekday


@pytest.mark.parametrize(
    "date, expected", [
        (None, {
            "День недели": ["Понедельник", "Вторник", "Среда", "Суббота", "Воскресенье"],
            "Средние траты": [1232.0, 300.0, 854.0, 6086.48, 1711.5]
        }),
        ("02.02.2025", {
            "День недели": ["Понедельник", "Вторник", "Среда", "Суббота", "Воскресенье"],
            "Средние траты": [1200.0, 300.0, 1256.0, 1794.0, 1711.5]
        })
    ]
)
def test_spending_by_weekday(date, expected, transactions):
    mock_date_obj = Mock(return_value=datetime.datetime.strptime("01.04.2025", "%d.%m.%Y"))
    datetime.today = mock_date_obj
    assert spending_by_weekday(transactions, date) == json.dumps(expected, ensure_ascii=False, indent=4)
