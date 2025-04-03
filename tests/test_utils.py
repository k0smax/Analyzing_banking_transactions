import datetime
import json
from json import JSONDecodeError
from unittest.mock import Mock, patch, mock_open

import pandas as pd
import pytest

from src.utils import reader_xlsx, reader_json, get_start_date, data_sorted_by_date, get_total_amount, \
    rename_and_convert_to_dict, get_expenses, get_income, get_currency_rates, get_stocks_prices


# Наименование тестов в следующем формате 'test_{имя_тестируемой_функции}_{дополнительное_уточнение(не обязательно)}'
@patch("src.utils.utils_logger")
def test_reader_xlsx(mock_logger, tests_data_for_readers):
    """
    Тест для проверки правильной работы функции reader_xlsx
    """
    return_value = pd.DataFrame(tests_data_for_readers)

    with patch("os.path.join", return_value="file_name.xlsx"):
        with patch("pandas.read_excel", return_value=return_value):
            result = reader_xlsx("file_name.xlsx")
            pd.testing.assert_frame_equal(result, pd.DataFrame(tests_data_for_readers))

            mock_logger.info.assert_called_once_with("Успешное считывание файла file_name.xlsx")


@patch("src.utils.utils_logger")
def test_reader_xlsx_file_not_found(mock_logger):
    """
    Тест для обработки FileNotFoundError в функции reader_xlsx и возврата пустого DataFrame.
    """
    # Мокируем os.path.join и pd.read_excel
    with patch("os.path.join", return_value="non_existent_file.xlsx"):
        with patch("pandas.read_excel", side_effect=FileNotFoundError("Файл не найден")):
            # Вызываем функцию и проверяем результат
            result = reader_xlsx("non_existent_file.xlsx")
            pd.testing.assert_frame_equal(result, pd.DataFrame({}))

            mock_logger.error.assert_called_once_with("Ошибка в чтении файла! Файл не найден")


@patch("src.utils.utils_logger")
def test_reader_json(mock_logger, tests_data_for_readers):
    """
    Тест для проверки правильной работы функции reader_json
    """
    return_value = tests_data_for_readers
    with patch("os.path.join", return_value="file_name.json"):
        with patch("builtins.open", mock_open(read_data=json.dumps(return_value, ensure_ascii=False))):
            with patch("json.load", return_value=return_value):
                result = reader_json("file_name.json")
                assert result == tests_data_for_readers

                mock_logger.info.assert_called_once_with(f"Успешное считывание файла file_name.json")


@patch("src.utils.utils_logger")
def test_reader_json_file_not_found(mock_logger):
    """
    Тест для обработки FileNotFoundError в функции reader_json и возврата пустого словаря.
    """
    with patch("os.path.join", return_value="non_existent_file.json"):
        with patch("builtins.open", side_effect=FileNotFoundError("Файл не найден")):
            # Вызываем функцию и проверяем результат
            result = reader_json("non_existent_file.json")
            assert result == {}

            mock_logger.error.assert_called_once_with("Ошибка в чтении файла! Файл не найден")


@pytest.mark.parametrize(
    "error_typy, json_data, error_message",
    [
        (JSONDecodeError, "{'key': 'value'", "Expecting ',' delimiter"),
        (TypeError, {"key": "value"}, "Некорректный тип данных"),
        (ValueError, 'value', "Некорректное значение")
    ]
)
@patch("src.utils.utils_logger")
def test_reader_json_file_not_json_data(mock_logger, error_typy, json_data, error_message):
    """
    Тест для обработки (JSONDecodeError, TypeError, KeyError, ValueError) в функции reader_json
     и возврата пустого словаря.
    """
    with patch("os.path.join", return_value="file_name.json"):
        with patch("builtins.open", mock_open(read_data=json.dumps(json_data, ensure_ascii=False))):
            with patch("json.load", side_effect=error_typy(error_message, "file_name.json", 1)):
                # Вызываем функцию и проверяем результат
                result = reader_json("file_name.json")
                assert result == {}

            mock_logger.error.assert_called_once()


@pytest.mark.parametrize(
    "range_date, expected", [
        ("W", "17.03.2025"),
        ("M", "01.03.2025"),
        ("Y", "01.01.2025"),
        ("All", None),
        (None, None),
        ("T", None)  # Несуществующий ключ
    ]
)
def test_get_start_date(range_date, expected, get_date_string):
    """
    Тест для проверки правильной работы функции get_start_date
    """
    assert get_start_date(get_date_string, range_date) == expected


# @pytest.mark.parametrize(
#     "start_date, finish_date, expected", [
#         ("20.02.2025", "01.03.2025", {
#             "Дата без времени": ["20.02.2025", "01.03.2025"],
#             "Дата операции": ["20.02.2025 13:40:00", "01.03.2025 19:55:00"],
#             "Сумма операции": [1000.00, -50.00],
#             "Категория": ["Супермаркеты", "Кино"]
#         }),
#         (None, "15.01.2025", {
#             "Дата без времени": ["01.01.2025", "05.01.2025", "10.01.2025", "15.01.2025"],
#             "Дата операции": [
#                 "01.01.2025 10:00:00", "05.01.2025 14:30:00", "10.01.2025 09:15:00", "15.01.2025 18:45:00"
#             ],
#             "Сумма операции": [1000.00, -2500.50, 750.00, -1200.00],
#             "Категория": ["Супермаркеты", "АЗС", "Рестораны", "Одежда"]
#         }),
#         (None, None, {
#             "Дата без времени": [
#                 "01.01.2025", "05.01.2025", "10.01.2025",
#                 "15.01.2025", "20.01.2025", "25.01.2025",
#                 "01.02.2025", "05.02.2025", "20.02.2025",
#                 "01.03.2025"
#             ],
#             "Дата операции": [
#                 "01.01.2025 10:00:00", "05.01.2025 14:30:00", "10.01.2025 09:15:00",
#                 "15.01.2025 18:45:00", "20.01.2025 12:00:00", "25.01.2025 16:20:00",
#                 "01.02.2025 11:10:00", "05.02.2025 17:30:00", "20.02.2025 13:40:00",
#                 "01.03.2025 19:55:00"
#             ],
#             "Сумма операции": [
#                 1000.00, -2500.50, 750.00, -1200.00, 500.00, -300.00, 1500.00,
#                 -200.00, 1000.00, -50.00
#             ],
#             "Категория": [
#                 "Супермаркеты", "АЗС", "Рестораны", "Одежда", "Транспорт", "Развлечения",
#                 "Аптеки", "Кафе", "Супермаркеты", "Кино"
#             ]
#         })
#     ]
# )
# def test_data_sorted_by_date(start_date, finish_date, expected, transactions):
#     keys = ["Дата операции", "Сумма операции", "Категория"]
#     transactions_filtered = pd.DataFrame({x: transactions[x] for x in keys})
#     result = data_sorted_by_date(transactions_filtered, start_date, finish_date)
#     pd.testing.assert_frame_equal(result, pd.DataFrame(expected))
#     tr = {x: transactions[x]}


@pytest.mark.parametrize(
    "start_date, finish_date, start_index, finish_index", [
        ("20.02.2025", "01.03.2025", 13, 19),
        (None, "15.01.2025", 0, 3),
        (None, None, 0, 19)
    ]
)
def test_data_sorted_by_date(start_date, finish_date, start_index, finish_index, transactions):
    """
    Тест для проверки работы функции data_sorted_by_date
    """
    # Формируем DataFrame с необходимыми колонками и вычисляем результат работы функции
    keys = ["Дата операции", "Сумма операции", "Категория"]
    transactions_filtered = pd.DataFrame({x: transactions[x] for x in keys})
    result = data_sorted_by_date(transactions_filtered, start_date, finish_date)

    # Создаем словарь с ожидаемым результатом
    expected_result = {key: [val
                             for index, val in enumerate(value) if index in range(start_index, finish_index + 1)]
                       for key, value in transactions.items() if key in keys}
    expected_result["Дата без времени"] = [datetime.datetime.strptime(val[:10], "%d.%m.%Y")
                                           for index, val in enumerate(transactions.get("Дата операции"))
                                           if index in range(start_index, finish_index + 1)]

    pd.testing.assert_frame_equal(result, pd.DataFrame(expected_result))


def test_get_total_amount(transactions):
    """
    Тест для проверки работы функции get_total_amount
    """
    assert get_total_amount(pd.DataFrame({"Сумма операции с округлением": []})) == 0.0
    assert get_total_amount(pd.DataFrame(transactions)) == 33217.45


def test_rename_and_convert_to_dict(transactions):
    """
    Тест для проверки работы функции rename_and_convert_to_dict
    """
    operations = pd.DataFrame({
        "Категория": ["Кино", "Супермаркеты"],
        "Сумма операции с округлением": [105.0, 434.2]
    })
    assert rename_and_convert_to_dict(operations) == [
        {"category": "Кино", "amount": 105.0},
        {"category": "Супермаркеты", "amount": 434.2},
    ]

    assert  rename_and_convert_to_dict(pd.DataFrame({"Категория": [], "Сумма операции с округлением": []})) == []


def test_get_expenses(transactions):
    """
    Тест для проверки работы функции get_expenses
    """
    result = get_expenses(transactions)
    assert result == (27316.45,
                      [
                          {'category': 'Одежда', 'amount': 13730.0},
                          {'category': 'Супермаркеты', 'amount': 3554.0},
                          {'category': 'АЗС', 'amount': 2500.0},
                          {'category': 'Аптеки', 'amount': 2360.0},
                          {'category': 'Кафе', 'amount': 1600.0},
                          {'category': 'Развлечения', 'amount': 450.0},
                          {'category': 'Транспорт', 'amount': 358.0}],
                      [
                          {'category': 'Переводы', 'amount': 1564.0},
                          {'category': 'Наличные', 'amount': 1200.0}]
                      )


def test_get_income(transactions):
    """
    Тест для проверки работы функции get_income
    """
    result = get_income(transactions)
    assert result == (1300.0,
                      [
                          {'category': 'Наличные', 'amount': 800.0},
                          {'category': 'Пополнения', 'amount': 500.0}]
                      )


@pytest.mark.parametrize(
    "usd_rate, eur_rate, expected", [
        (85.34, 95.65, [{"currency": "USD", "rate": 85.34}, {"currency": "EUR", "rate": 95.65}]),
        (None, 95.65, [{"currency": "USD", "rate": None}, {"currency": "EUR", "rate": 95.65}]),
        (None, None, [{"currency": "USD", "rate": None}, {"currency": "EUR", "rate": None}]),
    ]
)
@patch("requests.get")
def test_get_currency_rates(mock_requests, usd_rate, eur_rate, expected, user_currencies_test):
    """
    Тест для проверки работы функции get_currency_rates
    """
    mock_response_usd = Mock()
    mock_response_usd.json.return_value = {"result": usd_rate}

    mock_response_eur = Mock()
    mock_response_eur.json.return_value = {"result": eur_rate}

    mock_requests.side_effect = [mock_response_usd, mock_response_eur]
    result = get_currency_rates(user_currencies_test)

    assert result == expected


@pytest.mark.parametrize(
    "stock_1, stock_2, expected", [
        (115.45, 326.78, [{"stock": "AAPL", "price": 115.45}, {"stock": "AMZN", "price": 326.78}]),
        (115.45, None, [{"stock": "AAPL", "price": 115.45}, {"stock": "AMZN", "price": None}]),
        (None, None, [{"stock": "AAPL", "price": None}, {"stock": "AMZN", "price": None}]),
    ]
)
@patch("requests.get")
def test_get_stocks_prices(mock_requests, stock_1, stock_2, expected, user_stocks_test):
    """
    Тест для проверки работы функции get_stocks_prices
    """
    mock_response_stock_1 = Mock()
    mock_response_stock_1.json.return_value = {"price": stock_1}

    mock_response_stock_2 = Mock()
    mock_response_stock_2.json.return_value = {"price": stock_2}

    mock_requests.side_effect = [mock_response_stock_1, mock_response_stock_2]
    result = get_stocks_prices(user_stocks_test)

    assert result == expected
