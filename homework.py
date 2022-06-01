import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(message)s',
    filemode='a'
)

PRACTICUM_TOKEN = os.getenv('P_TOKEN')
TELEGRAM_TOKEN = os.getenv('TG_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_TIME = 10
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logging.info(f'Отправлено сообщение {message}')


def get_api_answer(current_timestamp):
    """Запрос к эндпоинту API."""
    response = requests.get(
        url=ENDPOINT,
        headers=HEADERS,
        params={'from_date': current_timestamp}
    )
    if response.status_code == HTTPStatus.OK:
        return response.json()
    raise TypeError('Нет ответа от API')


def check_response(response):
    """Вывод списка работ."""
    if type(response['homeworks']) != list:
        raise TypeError('Передается не тот тип')
    return response['homeworks']


def parse_status(homework):
    """Создание нужного сообщения."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]
    for work in HOMEWORK_STATUSES.keys():
        if work in homework_status:
            return (f'Изменился статус проверки '
                    f'работы "{homework_name}". {verdict}')
    logging.error('Недокументированный статус домашней работы')
    raise TypeError('Отсутствуют нужные элементы')


def check_tokens():
    """Проверка токенов и id чата."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствует токен, либо id чата')
        raise TypeError('Отсутствие необходимых данных')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0
    while True:
        try:
            response = get_api_answer(current_timestamp)
            if len(response['homeworks']) != 0:
                homework = check_response(response)[0]
                message = parse_status(homework)
                send_message(bot, message)
                current_timestamp = (response['current_date']
                                     or int(time.time()))
            logging.error('Список homeworks пустой')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        else:
            logging.error('Сообщение не отправлено')
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
