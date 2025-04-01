import datetime
import json
import logging
import os

import pandas as pd

from config import PATH_TO_PROJECT
from src.utils import data_sorted_by_date, reader_xlsx

services_logger = logging.getLogger("services")
services_logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(os.path.join(PATH_TO_PROJECT, "logs/services.log"), mode="w", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(funcName)s: %(message)s")
file_handler.setFormatter(file_formatter)
services_logger.addHandler(file_handler)


def investment_bank(month: str, transactions: list[dict], limit: int) -> str:
    """
    Функция рассчитывает сумму, которую удалось бы отложить в «Инвесткопилку»
    :param month: месяц, для которого рассчитывается отложенная сумма (строка в формате 'YYYY-MM')
    :param transactions: список словарей, содержащий информацию о транзакциях, в которых содержатся следующие поля:
        Дата операции — дата, когда произошла транзакция (строка в формате 'YYYY-MM-DD').
        Сумма операции — сумма транзакции в оригинальной валюте (число).
    :param limit: предел, до которого нужно округлять суммы операций (целое число)
    :return: сумма, которую удалось бы отложить в «Инвесткопилку»
    """
    # Определяем дату начала месяца
    services_logger.info("Определение даты начала месяца")
    start_date_obj = pd.to_datetime(month)
    start_date_str = datetime.datetime.strftime(start_date_obj, "%d.%m.%Y")
    services_logger.info(f"Дата начала месяца - {start_date_str}")

    # Определяем дату последнего дня месяца
    services_logger.info("Определение даты последнего дня месяца")
    finish_date_obj = start_date_obj + pd.offsets.MonthEnd(1)
    finish_date_str = datetime.datetime.strftime(finish_date_obj, "%d.%m.%Y")
    services_logger.info(f"Дата последнего дня месяца - {finish_date_str}")

    # Отсортированные по месяцу транзакции
    services_logger.info("Сортировка транзакций по месяцу")
    sorted_transactions_by_month = data_sorted_by_date(pd.DataFrame(transactions), start_date_str, finish_date_str)
    services_logger.info("Транзакции по месяцу успешно отсортированы")

    services_logger.info("Расчет выгоды при использовании Инвесткопилки")
    # Приведение суммы операций к положительному значению
    sorted_transactions_by_month.loc[:, "Сумма операции"] = sorted_transactions_by_month["Сумма операции"].abs()

    # Добавление новой колонки для расчета возможной выгоды при использовании Инвесткопилки
    sorted_transactions_by_month.loc[:, "Инвесткопилка"] = limit - (
        sorted_transactions_by_month["Сумма операции"] % limit
    )

    # Расчет выгоды при использовании Инвесткопилки
    investment = round(sorted_transactions_by_month["Инвесткопилка"].sum(), 2)

    services_logger.info("Расчет выгоды при использовании Инвесткопилки завершен")
    return json.dumps(investment)


if __name__ == "__main__":
    transactions = reader_xlsx("data/operations.xlsx").to_dict(orient="records")
    # print(transactions.to_dict(orient="records"))
    print(investment_bank("2020-01", transactions, 10))
