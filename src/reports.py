import json
import logging
import os
from datetime import datetime
from functools import wraps
from time import time
from typing import Any, Callable, Optional

import pandas as pd
from dateutil.relativedelta import relativedelta

from config import PATH_TO_PROJECT
from src.utils import data_sorted_by_date, reader_xlsx

reports_logger = logging.getLogger("reports")
reports_logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(os.path.join(PATH_TO_PROJECT, "logs/reports.log"), mode="w", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(funcName)s: %(message)s")
file_handler.setFormatter(file_formatter)
reports_logger.addHandler(file_handler)


def recording_decorator(func):
    """
    Декоратор, который записывает данные отчета в файл с названием по умолчанию
    :param func: любая функция
    :return: ссылка на внутреннюю функцию wrapper
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        result_dict = json.loads(result)
        result_dict["Имя функции"] = func.__name__
        with open(os.path.join(PATH_TO_PROJECT, "reports/reports.json"), "w", encoding="UTF-8") as file:
            json.dump(result_dict, file, ensure_ascii=False, indent=4)
        return result

    return wrapper


def recording_in_filename_decorator(filename: str) -> Callable:
    """
    Декоратор, который записывает данные отчета в файл с названием 'filename'
    :param filename: любая функция
    :return: ссылка на внутреннюю функцию wrapper
    """

    def inner(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            result_dict = json.loads(result)
            result_dict["Имя функции"] = func.__name__
            with open(os.path.join(PATH_TO_PROJECT, f"reports/{filename}.json"), "w", encoding="UTF-8") as file:
                json.dump(result_dict, file, ensure_ascii=False, indent=4)
            return result

        return wrapper

    return inner


def timer_decorator(func: Callable) -> Callable:
    """
    Декоратор, который считает время выполнения функции
    :param func: любая функция
    :return: ссылка на внутреннюю функцию wrapper
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        time_1 = time()
        result = func(*args, **kwargs)
        time_2 = time()
        print(f"Время работы функции: {time_2 - time_1}")
        return result

    return wrapper


@recording_in_filename_decorator("reports_file")
@recording_decorator
@timer_decorator
def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str] = None) -> str:
    """
    Функция формирует отчет по средним тратам в каждый из дней недели за последние три месяца (от переданной даты)
    :param transactions: анализируемые транзакции в формате DataFrame
    :param date: верхняя граница даты для проведения анализа по транзакциям
    :return: json-строка, содержащая средние траты в каждый из дней недели за последние три месяца
    """
    reports_logger.info("Определение даты для проведения анализа по транзакциям")
    if date is None:
        date_obj = datetime.today()
    else:
        date_obj = datetime.strptime(date, "%d.%m.%Y")

    # Определяем начальный и конечный день, в диапазоне которых необходимо проанализировать транзакции
    reports_logger.info("Определение начальной и конечной день для анализа транзакций")
    date_finish_str = date_obj.strftime("%d.%m.%Y")
    date_start_obj = date_obj - relativedelta(months=3)
    date_start_str = date_start_obj.strftime("%d.%m.%Y")
    reports_logger.info(f"Начальный день - {date_start_str}, конечный день - {date_finish_str}")

    # Фильтруем транзакции по дате
    reports_logger.info("Фильтрация транзакций по диапазону дат")
    transactions = data_sorted_by_date(transactions, date_start_str, date_finish_str)
    reports_logger.info("Транзакции успешно отфильтрованы")

    # Фильтруем транзакции по условиям
    transactions = transactions.loc[
        (transactions["Сумма операции"] < 0) & (transactions["Статус"] == "OK")
    ].reset_index()
    transactions = transactions.groupby("Дата без времени")["Сумма операции с округлением"].sum().reset_index()

    # Создаем словарь соответствия номера дня недели и дня недели
    number_weekdays = {
        0: "Понедельник",
        1: "Вторник",
        2: "Среда",
        3: "Четверг",
        4: "Пятница",
        5: "Суббота",
        6: "Воскресенье",
    }

    # # Создаем словарь, который будет хранить сумму трат и количество трат в каждый день недели
    # result = {
    #     "Понедельник": {
    #         "expense": 0,
    #         "count": 0
    #     },
    #     "Вторник": {
    #         "expense": 0,
    #         "count": 0
    #     },
    #     "Среда": {
    #         "expense": 0,
    #         "count": 0
    #     },
    #     "Четверг": {
    #         "expense": 0,
    #         "count": 0
    #     },
    #     "Пятница": {
    #         "expense": 0,
    #         "count": 0
    #     },
    #     "Суббота": {
    #         "expense": 0,
    #         "count": 0
    #     },
    #     "Воскресенье": {
    #         "expense": 0,
    #         "count": 0
    #     }
    # }
    #
    # for index, transaction in transactions.iterrows():
    #     # Получаем дату операции
    #     date_time_str = transaction["Дата без времени"]
    #
    #     date_time_obj = datetime.strptime(date_time_str, "%d.%m.%Y")
    #
    #     # Получаем день недели
    #     weekday = date_time_obj.weekday()
    #
    #     # Обновляем сумму операции соответствующего дня недели и увеличиваем количество текущего дня недели на 1
    #     result[number_weekdays[weekday]]["expense"] += transaction["Сумма операции с округлением"]
    #     result[number_weekdays[weekday]]["count"] += 1
    #
    # # Возвращаем результат в виде DataFrame
    # return pd.DataFrame({
    #     "День недели": [day for day in result.keys()],
    #     "Среднее значение трат": [round(result[day]["expense"] / result[day]["count"], 2) for day in result.keys()]
    # })
    #
    # Добавляем новые колонки, соответствующие номеру дня недели и дню недели
    # transactions["Номер дня недели"] = transactions.apply(
    #     lambda x: datetime.strptime(x["Дата без времени"], "%d.%m.%Y").weekday(), axis = 1)
    # transactions["День недели"] = transactions.apply(
    #     lambda x: number_weekdays[x["Номер дня недели"]], axis = 1)
    # transactions["Номер дня недели"] = transactions.apply(lambda x: datetime.strptime(x["Дата операции"],
    # "%d.%m.%Y %H:%M:%S").weekday(), axis = 1)
    # Добавляем новый столбец
    transactions["День недели"] = transactions.apply(lambda x: x["Дата без времени"].weekday(), axis=1).map(
        number_weekdays
    )

    # Группируем по дню недели и считаем среднее
    transactions = transactions.groupby("День недели")["Сумма операции с округлением"].mean().round(2).reset_index()

    # Сортируем по дням недели
    transactions["День недели"] = pd.Categorical(
        transactions["День недели"], categories=number_weekdays.values(), ordered=True
    )
    transactions = transactions.sort_values("День недели").reset_index(drop=True)

    result_json = json.dumps(
        transactions.rename(columns={"Сумма операции с округлением": "Средние траты"}).to_dict("list"),
        ensure_ascii=False,
        indent=4,
    )
    reports_logger.info("Отчет по транзакциям успешно сформирован")
    return result_json


if __name__ == "__main__":
    data = reader_xlsx("data/operations.xlsx")
    print(spending_by_weekday(data, "02.02.2020"))
