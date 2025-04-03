import datetime
import json
import logging
import os

from config import PATH_TO_PROJECT
from src.reports import spending_by_weekday
from src.services import investment_bank
from src.utils import reader_xlsx
from src.views import get_events

main_logger = logging.getLogger("main")
main_logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(os.path.join(PATH_TO_PROJECT, "logs/main.log"), mode="w", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(funcName)s: %(message)s")
file_handler.setFormatter(file_formatter)
main_logger.addHandler(file_handler)

# Путь файла с транзакциями
file_path = "data/operations.xlsx"

# Подгружаем транзакции из файла
main_logger.info(f"Получение транзакций из файла {file_path}")
transactions = reader_xlsx(file_path)
main_logger.info(f"Данные из файла {file_path} успешно прочитаны")

# Определяем начальный и конечный день транзакций, полученных из файла
transactions["Дата без времени"] = (
    transactions["Дата операции"].apply(lambda x: x[:10]).apply(lambda x: datetime.datetime.strptime(x, "%d.%m.%Y"))
)
start_day_str = transactions["Дата без времени"].min().strftime("%Y-%m-%d")
finish_day_str = transactions["Дата без времени"].max().strftime("%Y-%m-%d")

transactions = transactions.drop("Дата без времени", axis=1)

print(f"Транзакции успешно подгружены. " f"Диапазон дат транзакций: {start_day_str} - {finish_day_str}")

user_finish_date_str = input("Введите дату в формате dd.mm.YYYY, до который необходимо провести анализ транзакций: ")
user_range_date = input(
    "Введите период за который необходимо провести анализ транзакций (неделя, месяц, год, весь период): "
)
if user_range_date.lower() == "неделя":
    range_date = "W"
elif user_range_date.lower() == "год":
    range_date = "Y"
elif user_range_date.lower() == "весь период":
    range_date = "All"
else:
    range_date = "M"

events = get_events(transactions, user_finish_date_str, range_date)
main_logger.info("Успешно получена информация по странице События")

main_logger.info("Рассчитываем выгоду по Инвесткопилке")
print(
    "Вы можете посчитать, сколько могли бы накопить денег,"
    " если бы использовали сервис Инвесткопилку в предыдущем месяце"
)
user_month = input(
    "За какой месяц вы желаете получить информацию по сервису Инвесткопилка?" "Введите дату в формате YYYY-MM: "
)

investment_limit_5 = investment_bank(user_month, transactions.to_dict(orient="records"), 5)
investment_limit_10 = investment_bank(user_month, transactions.to_dict(orient="records"), 10)
investment_limit_50 = investment_bank(user_month, transactions.to_dict(orient="records"), 50)
main_logger.info("Успешно рассчитана выгода по Инвесткопилке")

print(f"Если бы вы округляли сумму до 5 рублей, то получили бы выгоду {investment_limit_5}")
print(f"Если бы вы округляли сумму до 10 рублей, то получили бы выгоду {investment_limit_10}")
print(f"Если бы вы округляли сумму до 50 рублей, то получили бы выгоду {investment_limit_50}")

main_logger.info("Расчет расходов по дням недели")
print("Давайте посчитаем, сколько вы тратили денег по дням недели за последние три месяца")
spending_by_weekday = json.loads(spending_by_weekday(transactions, ".".join(reversed(finish_day_str.split("-")))))

main_logger.info("Расчет расходов по дням недели успешно выполнен")

for i in range(len(spending_by_weekday.get("День недели", []))):
    print(f"{spending_by_weekday['День недели'][i]}: {spending_by_weekday['Средние траты'][i]}")
