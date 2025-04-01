# РАЗДЕЛ СОБЫТИЯ
import datetime
import json
import logging
import os

import pandas as pd

from config import PATH_TO_PROJECT
from src.utils import (data_sorted_by_date, get_currency_rates, get_expenses, get_income, get_start_date,
                       get_stocks_prices, reader_json, reader_xlsx)

views_logger = logging.getLogger("views")
views_logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(os.path.join(PATH_TO_PROJECT, "logs/views.log"), mode="w", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(funcName)s: %(message)s")
file_handler.setFormatter(file_formatter)
views_logger.addHandler(file_handler)


def get_events(transactions: pd.DataFrame, finish_date_string: str, range_date: str = "M") -> str:
    """
    Основная функция, формирующая json-строку с данными для страницы "События"
    :param finish_date_string: дата (соответствует верхней границе) в формате dd.mm.YYYY !!!
    :param range_date: диапазон, за который проводится анализ (по умолчанию один месяц - с начала месяца,
    на который выпадает дата, по саму дату date_string.
    Возможные значения параметра:
    W — неделя, на которую приходится дата;
    M — месяц, на который приходится дата;
    Y — год, на который приходится дата;
    ALL — все данные до указанной даты.
    :return: json-строка с данными о расходах, поступлениях, курсах валют и о стоимости акций S&P500
    """
    views_logger.info("Расчет верхней границы даты")
    # Пытаемся получить объект datetime из строки date_string.
    if not datetime.datetime.strptime(finish_date_string, "%d.%m.%Y"):
        views_logger.error("Ошибка! Формат даты неверный!")
        finish_date_string = None

    views_logger.info(f"Верхняя граница даты успешно определена - {finish_date_string}")

    # Рассчитываем стартовый день с которого необходимо проводить анализ по транзакциям
    views_logger.info("Рассчитываем стартовый день с которого необходимо проводить анализ по транзакциям")
    start_date_string = get_start_date(finish_date_string, range_date)
    views_logger.info(
        "Стартовый день с которого необходимо проводить анализ по транзакциям определен" f" - {start_date_string}]"
    )

    # Транзакции, отсортированные по заданному диапазону дат
    views_logger.info(f"Сортировка транзакций по диапазону дат {range_date}")
    transactions_sorted_by_date = data_sorted_by_date(transactions, start_date_string, finish_date_string)
    views_logger.info(f"Сортировка транзакций по диапазону дат {range_date} произведена")

    # Получаем результат анализа транзакций по блокам расходов и поступлений
    views_logger.info("Анализ транзакций по блокам расходов и поступлений")
    total_amount_expense, main_block_expense, transfers_and_cash_block = get_expenses(transactions_sorted_by_date)
    total_amount_income, main_block_income = get_income(transactions_sorted_by_date)
    views_logger.info("Анализ транзакций по блокам расходов и поступлений успешно завершен")

    # Подгружаем список валют и акций
    user_currencies = reader_json("user_settings.json").get("user_currencies", [])
    user_stocks = reader_json("user_settings.json").get("user_stocks", [])

    # Получаем курсы валют
    views_logger.info("Получение курса валют")
    currency_rates = get_currency_rates(user_currencies)

    # Получаем стоимость акций
    views_logger.info("Получение стоимости акций")
    stock_prices = get_stocks_prices(user_stocks)

    response_dict = {
        "expenses": {
            "total_amount": round(total_amount_expense),
            "main": main_block_expense,
            "transfers_and_cash": transfers_and_cash_block,
        },
        "income": {"total_amount": round(total_amount_income), "main": main_block_income},
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }

    # Преобразуем словарь в json-ответ
    result_json = json.dumps(response_dict, ensure_ascii=False)
    views_logger.info("Данные для страницы События успешно сформированы")

    return result_json


if __name__ == "__main__":
    # print(get_events("30.11.2021"))
    data = reader_xlsx("data/operations.xlsx")
    print(get_events("07.02.2025", "Y"))
    # print(data_sorted_by_date(data, "23.11.2020", "27.11.2020"))
    # print(get_start_date(None, "W"))
    # print(get_income(data))
