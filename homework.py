import os
import logging

from dotenv import load_dotenv
import requests
import telegram
import time

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

RETRY_TIME = 3600
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
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': 0}
    response = requests.get(
        url=ENDPOINT,
        headers=HEADERS,
        params=params
    )
    if response.status_code == 200:
        return response.json()
    else:
        logging.error('Нет ответа от API')
        raise TypeError('Нет ответа от API')


def check_response(response):
    """Вывод списка работ."""
    if type(response['homeworks']) != list:
        raise TypeError('Передается не тот тип')
    if not response['homeworks']:
        logging.error('Список homework пустой')
        raise TypeError('Обновлений нет')
    return response['homeworks']


def parse_status(homework):
    """Создание нужного сообщения."""
    homework_name = homework[0]['homework_name']
    homework_status = homework[0]['status']
    verdict = HOMEWORK_STATUSES[homework_status]
    if ('approved' in homework_status
            or 'reviewing' in homework_status
            or 'rejected' in homework_status):
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        logging.error('Недокументированный статус домашней работы')
        raise TypeError('Отсутствуют нужные элементы')


def check_tokens():
    """Проверка токенов и id чата."""
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
        logging.critical('Отсутствует токен, либо id чата')
        raise TypeError('Отсутствие необходимых данных')
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if len(homework) != 0:
                message = parse_status(homework)
                send_message(bot, message)
                time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            logging.error('Сообщение не отправлено')
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
