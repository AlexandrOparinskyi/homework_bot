import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(message)s',
    filemode='a'
)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('P_TOKEN')
TELEGRAM_TOKEN = os.getenv('TG_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения"""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logging.info(f'Отправлено сообщение: {message}')


def get_api_answer(current_timestamp):
    """Запрос к эндпоинту API"""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(
        url=ENDPOINT,
        headers=HEADERS,
        params=params
    )
    if response.status_code != 200:
        logging.error('Нет ответа от API')
    return response.json() or False


def check_response(response):
    """Вывод списка работ"""
    return response['homeworks']


def parse_status(homework):
    """Создание нужного сообщения"""
    homework_name = homework[0].get('homework_name')
    homework_status = homework[0].get('status')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов и id чата"""
    if (PRACTICUM_TOKEN is not None
            and TELEGRAM_TOKEN is not None
            and TELEGRAM_CHAT_ID is not None):
        return True
    else:
        return False


def main():
    """Основная логика работы бота."""
    if check_tokens() is True:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        current_timestamp = int(time.time())
    else:
        logging.critical('Отсутствуют обязательные переменные')
    while True:
        try:
            response = get_api_answer(current_timestamp)
            if response is False:
                logging.error('С API что-то не так')
            print(response)
            homework = check_response(response)
            if len(homework) != 0:
                message = parse_status(homework)
                send_message(bot, message)
                time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logging.error(f'Сбой при отправке сообщения. Ошибка: {error}')
            time.sleep(RETRY_TIME)
        else:
            logging.info('Работу не проверили')
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
