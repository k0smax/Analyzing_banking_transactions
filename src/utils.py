import datetime
import json
import logging
import os
from json import JSONDecodeError

import pandas as pd
import requests
from dotenv import load_dotenv

from config import PATH_TO_PROJECT

load_dotenv()

utils_logger = logging.getLogger("utils")
utils_logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(os.path.join(PATH_TO_PROJECT, "logs/utils.log"), mode="w", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(funcName)s: %(message)s")
file_handler.setFormatter(file_formatter)
utils_logger.addHandler(file_handler)


def reader_xlsx(path_to_file: str) -> pd.DataFrame:
    """
    Функция считывает файл с разрешением xlsx
    :param path_to_file: путь до файла
    :return: объект DataFrame
    """
    try:
        data = pd.read_excel(os.path.join(PATH_TO_PROJECT, path_to_file))
        utils_logger.info(f"Успешное считывание файла {os.path.join(PATH_TO_PROJECT, path_to_file)}")
    except FileNotFoundError as exp_info:
        utils_logger.error(f"Ошибка в чтении файла! {exp_info}")
        return pd.DataFrame({})
    return data


def reader_json(path_to_file: str) -> dict:
    """
    Функция считывает json-файл
    :param path_to_file: путь до файла
    :return: словарь с данными из json-файла
    """
    try:
        with open(os.path.join(PATH_TO_PROJECT, path_to_file)) as file:
            try:
                data = json.load(file)
                utils_logger.info(f"Успешное считывание файла {os.path.join(PATH_TO_PROJECT, path_to_file)}")
            except (JSONDecodeError, TypeError, ValueError) as exp_info:
                utils_logger.error(f"Ошибка! {exp_info}")
                return {}
    except FileNotFoundError as exp_info:
        utils_logger.error(f"Ошибка в чтении файла! {exp_info}")
        return {}
    return data


def get_start_date(finish_date_string: str | None, range_date: str) -> str | None:
    """
    Функция вычисляет начальную дату в зависимости от range_date.
    :param finish_date_string: дата, являющаяся верхней границей
    :param range_date: W - с начала недели, M - с начала месяца, Y - с начала года, All - весь период
    :return:    Если range_date == W, возвращается дата ближайшего прошедшего понедельника
    Если range_date == M, возвращается дата первого числа текущего месяца
    Если range_date == Y, возвращается дата первого января текущего года
    Если range_date == All, возвращается None
    """
    utils_logger.info("Запуск процесса расчета начальной даты.")
    # Проверяем на отсутствие даты. Если дата отсутствует, то возвращаем None
    if finish_date_string is None:
        utils_logger.warning(
            "Отсутствует верхняя граница даты! Начальная дата будет иметь значение None."
            "Проверьте правильность переданной даты!"
        )
        return None

    date_obj = datetime.datetime.strptime(finish_date_string, "%d.%m.%Y")
    if range_date == "W":
        date_obj = date_obj - datetime.timedelta(days=date_obj.weekday())
    elif range_date == "M":
        date_obj = date_obj.replace(day=1)
    elif range_date == "Y":
        date_obj = date_obj.replace(month=1, day=1)
    else:
        utils_logger.info(f"Начальная дата не имеет значения. Ключ диапазона - {range_date}.")
        return None

    utils_logger.info(f"Начальная дата имеет значение {date_obj}")
    start_date_string = date_obj.strftime("%d.%m.%Y")
    return start_date_string


def data_sorted_by_date(transactions: pd.DataFrame, start_date: str | None, finish_date: str | None) -> pd.DataFrame:
    """
    Функция фильтрует транзакции по диапазону дат, и возвращает транзакции только в определенном диапазоне дат
    :param data: данные с транзакциями за весь период
    :param start_date: начальная дата
    :param finish_date: конечная дата
    :return: возвращает новый DataFrame, отфильтрованный по диапазону дат
    """
    utils_logger.info(f"Запуск процесса сортировки данных в диапазоне дат {start_date} - {finish_date}.")
    # Добавляем новый столбец только с датой, форматируем его в datetime формат
    transactions["Дата без времени"] = (
        transactions["Дата операции"]
        .apply(lambda x: x[:10])
        .apply(lambda x: datetime.datetime.strptime(x, "%d.%m.%Y"))
    )

    # Проверяем, были ли переданы стартовая и конечная дата
    # Если данные были переданы, то конвертируем их в datetime-формат
    # Если нет, то стартовая дата равняется минимальной дате в колонке ["Дата без времени"], а конечная - макисмальной
    start_date = (
        datetime.datetime.strptime(start_date, "%d.%m.%Y") if start_date else transactions["Дата без времени"].min()
    )
    finish_date = (
        datetime.datetime.strptime(finish_date, "%d.%m.%Y") if finish_date else transactions["Дата без времени"].max()
    )

    try:
        # Фильтруем данные по диапазону дат
        data_sorted = transactions.loc[
            (transactions["Дата без времени"] <= finish_date) & (transactions["Дата без времени"] >= start_date)
        ]

        utils_logger.info("Процесс сортировки данных завершен.")
        return data_sorted.reset_index(drop=True)

    except Exception as exc_info:
        utils_logger.error(f"Ошибка при сортировке данных: {exc_info}", exc_info=True)
        return transactions


def get_total_amount(transactions: pd.DataFrame) -> int:
    """
    Функция рассчитывает общую сумму операций
    :param data: данные транзакций
    :return: сумма операций
    """
    utils_logger.info("Расчет общей суммы операций")
    return transactions["Сумма операции с округлением"].sum()


def rename_and_convert_to_dict(transactions: pd.DataFrame) -> list[dict]:
    """
    Функция переименовывает столбцы и преобразовывает DataFrame в список словарей
    :param data: входной DataFrame с колонками 'Категория' и 'Сумма операции с округлением'
    :return: список словарей с ключами 'category' и 'amount'
    """
    utils_logger.info("Преобразование DataFrame в список словарей")
    return transactions.rename(columns={"Категория": "category", "Сумма операции с округлением": "amount"}).to_dict(
        "records"
    )


def get_expenses(transactions: pd.DataFrame) -> tuple[int, list[dict], list[dict]]:
    """
    Функция формирует блок расходов
    :param transactions: входные данные, по которым проводится анализ
    :return: кортеж, содержащий общую сумму расходов и список категорий,
     отсортированный по убыванию по общей сумме расходов в каждой категории
    """
    utils_logger.info("Запущено формирование блока расходов")
    # Отбираем транзакции соответствующие расходам
    expense_operations = transactions.loc[(transactions["Сумма операции"] < 0) & (transactions["Статус"] == "OK")]

    # Рассчитываем общую сумму расходов
    total_amount_expense = get_total_amount(expense_operations)
    utils_logger.info("Рассчитана общая сумма расходов")

    # Группируем транзакции соответствующие расходам по категориям и считаем общую сумму расходов по каждой категории
    grouped_expense = (
        expense_operations.groupby("Категория")["Сумма операции с округлением"].sum().round().reset_index()
    )

    # Сортируем категории расходов по сумме операций в порядке убывания
    # за исключением категорий 'Наличные' и 'Переводы'
    main_block_expense = grouped_expense.loc[
        grouped_expense["Категория"].apply(lambda x: x not in ["Наличные", "Переводы"])
    ].sort_values("Сумма операции с округлением", ascending=False)

    # Сортируем категории расходов по сумме операций в порядке убывания по категориям 'Наличные' и 'Переводы'
    transfers_and_cash_block = grouped_expense.loc[
        grouped_expense["Категория"].isin(["Наличные", "Переводы"])
    ].sort_values("Сумма операции с округлением", ascending=False)

    # Оставляем первые семь категорий, у остальных подсчитываем сумму расходов и записываем её в категорию 'Остальное'
    if len(main_block_expense) > 7:
        other_amount = main_block_expense.iloc[7:]["Сумма операции с округлением"].sum()
        main_block_expense = pd.concat(
            [
                main_block_expense.iloc[:7],
                pd.DataFrame([{"Категория": "Остальное", "Сумма операции с округлением": other_amount}]),
            ]
        )

    # Формируем блок расходов ('expense[main]') в соответствии с техническим заданием
    main_block_expense = rename_and_convert_to_dict(main_block_expense)
    utils_logger.info("Сформирован main-подблок блока расходов")

    # Формируем блок расходов ('expense[transfers_and_cash]') в соответствии с техническим заданием
    transfers_and_cash_block = rename_and_convert_to_dict(transfers_and_cash_block)
    utils_logger.info("Сформирован transfers_and_cash-подблок блока расходов")

    utils_logger.info("Успешное формирование блока расходов")
    return total_amount_expense, main_block_expense, transfers_and_cash_block


def get_income(transactions: pd.DataFrame) -> tuple[int, list[dict]]:
    """
    Функция формирует блок расходов
    :param transactions: входные данные, по которым проводится анализ
    :return: кортеж, содержащий общую сумму пополнений и список категорий,
     отсортированный по убыванию по общей сумме пополнений в каждой категории
    """
    utils_logger.info("Запущено формирование блока поступлений")
    # Отбираем транзакции соответствующие пополнению
    income_operations = transactions.loc[(transactions["Сумма операции"] > 0) & (transactions["Статус"] == "OK")]

    # Рассчитываем общую сумму пополнений
    total_amount_income = get_total_amount(income_operations)
    utils_logger.info("Рассчитана общая сумма поступлений")

    # Группируем транзакции соответствующие пополнению по категориям
    # и считаем общую сумму пополнений по каждой категории
    grouped_income = income_operations.groupby("Категория")["Сумма операции с округлением"].sum().round().reset_index()

    # Сортируем категории пополнений по сумме операций в порядке убывания
    main_block_income = grouped_income.sort_values("Сумма операции с округлением", ascending=False)

    # Формируем блок пополнений ('income[main]') в соответствии с техническим заданием
    main_block_income = rename_and_convert_to_dict(main_block_income)
    utils_logger.info("Сформирован main-подблок блока поступлений")

    utils_logger.info("Успешное формирование блока поступлений")
    return total_amount_income, main_block_income


def get_currency_rates(user_currencies: list) -> list[dict]:
    """
    Функция совершает API запрос с целью получения курса валют
    :param user_currencies: список валют по которым необходимо получить курс
    :return: список словарей с ключами 'currency' и 'rate'
    """
    utils_logger.info("Запущено формирование блока курса валют")
    # Загружаем api_key
    api_key = os.getenv("API_KEY_CURRENCY")

    # Создаем пустой словарь курса валют
    currency_rates = []

    # Запрос на получение курса валют
    amount = 1
    to_currency = "RUB"
    headers = {"apikey": api_key}

    # Проходим циклом по каждой валюте
    for currency in user_currencies:
        from_currency = currency
        url = (
            f"https://api.apilayer.com/exchangerates_data/convert?"
            f"to={to_currency}&from={from_currency}&amount={amount}"
        )
        try:
            utils_logger.info(f"Отправка запроса на получение курса {currency}")
            response = requests.get(url, headers=headers)
            rate = response.json().get("result")
            (
                currency_rates.append({"currency": currency, "rate": round(rate, 2)})
                if rate
                else currency_rates.append({"currency": currency, "rate": None})
            )
            utils_logger.info(f"Получена стоимость валюты! {currency} - {rate} RUB")
        except requests.RequestException as exc_info:
            utils_logger.error(f"Ошибка! {exc_info}", exc_info=True)
            currency_rates.append({})

    return currency_rates


def get_stocks_prices(user_stocks: list) -> list[dict]:
    """
    Функция совершает API запрос с целью получения стоимости акций
    :param user_stocks: список акций по которым необходимо узнать стоимость
    :return: список словарей с ключами 'stock' и 'price'
    """
    utils_logger.info("Запущено формирование блока стоимости акций S&P500")
    # Загружаем api_key
    api_key = os.getenv("API_KEY_STOCKS")

    # Создаем пустой словарь стоимости акций
    stock_prices = []

    # Запрос на получение курса валют
    headers = {"X-Api-Key": api_key}

    # Проходим циклом по каждой валюте
    for ticker in user_stocks:
        url = f"https://api.api-ninjas.com/v1/stockprice?ticker={ticker}"
        try:
            utils_logger.info(f"Отправка запроса на получение стоимости акции {ticker}")
            response = requests.get(url, headers=headers)
            # в долларах
            price = response.json().get("price")
            (
                stock_prices.append({"stock": ticker, "price": round(price, 2)})
                if price
                else stock_prices.append({"stock": ticker, "price": None})
            )
            utils_logger.info(f"Получена стоимость акции! {ticker} - {price}")
        except requests.RequestException as exc_info:
            utils_logger.error(f"Ошибка! {exc_info}", exc_info=True)
            stock_prices.append({})

    return stock_prices


if __name__ == "__main__":
    print(reader_xlsx("data/operations.xlsx"))
    # print(reader_json("user_settings.json"))
    # print(pd.DataFrame({"Столбец1": ["Один", "Два", "Три"]}))
    # print(get_income(pd.DataFrame(transactions)))
    # print(data_sorted_by_date(pd.DataFrame(transactions), "20.02.2025", "27.02.2025"))
    # print(get_currency_rates(["USD", "EUR"]))
    # print(get_stocks_prices(["AAPL", "AMZN"]))
