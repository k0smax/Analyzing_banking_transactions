import pytest

from src.services import investment_bank


@pytest.mark.parametrize(
    "month, limit, expected", [
        ("2025-02", 50, "260.0"),
        ("2025-02", 10, "50.0"),
        ("2025-01", 1, "8.0")
    ]
)
def test_investment_bank(transactions, month, limit, expected):
    result = investment_bank(month, transactions.to_dict(orient="records"), limit)
    assert result == expected
