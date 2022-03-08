import logging
import os
import sys
import time
from datetime import datetime
import requests

from dotenv import load_dotenv
from telegram import Bot

from exceptions import *


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler(stream=sys.stderr)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)

logger.addHandler(stream_handler)


def send_message(bot, message):
    """Отправляет сообщение `message` в указанный telegram-чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение в Telegram успешно отправлено')
    except Exception:
        logger.error(SendMessageFailureError())


def raise_and_log_error(exception):
    """Функция вызывает и логирует полученное исключение на уровне `ERROR`."""
    logger.error(exception)
    raise exception


def get_api_answer(current_timestamp):
    """
    Запрос к `API Yandex Practicum` с указанной временной меткой. В случае
    успешного запроса возвращает ответ API, приведенный к типам данных Python.
    """
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=headers, params=params)
    if homework_statuses.status_code == 404:
        raise_and_log_error(RequestError())
    elif homework_statuses.status_code != 200:
        raise_and_log_error(EndpointUnavailableError())
    return homework_statuses.json()


def check_response(response):
    """
    Проверка ответа API на корректность. При успешной проверке возвращает
    список домашних работ, доступный в ответе по ключу `homeworks`.
    """
    if not isinstance(response, dict):
        raise_and_log_error(TypeError(
            'Ответ сервиса не является словарем'
        ))
    try:
        homeworks = response.get('homeworks')
        if not isinstance(homeworks, list):
            raise_and_log_error(TypeError(
                'Содержимое ответа по ключу `homeworks` не является списком'
            ))
        if len(homeworks) == 0:
            raise_and_log_error(EmptyResponseError())
        return homeworks
    except KeyError:
        raise_and_log_error(KeyError(
            'В полученном ответе отсутствует ключ `homeworks`'
        ))


def parse_status(homework):
    """
    Функция извлекает статус работы из ответа Яндекс.Практикум и возвращает
    готовую строку для отправки пользователю.
    """
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if not (homework_status and homework_name):
        raise_and_log_error(KeyError(
            'В ответе отсутствуют ключи `homework_name` и/или `status`'
        ))
    verdict = HOMEWORK_STATUSES.get(homework_status)
    if not verdict:
        raise_and_log_error(WrongStatusError())
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """
    Проверка доступности необходимых переменных окружения.
    """
    tokens_exist = PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID
    if tokens_exist:
        return tokens_exist
    logger.critical(MissingTokenError())


def get_timestamp(report) -> int:
    """
    Функция в качестве параметра получает работу и возвращяет время последнего
    изменения статуса этой работы в формате Unix time.
    """
    report_update_date = report.get('date_updated')
    report_update_datetime = datetime.strptime(
        report_update_date, '%Y-%m-%dT%H:%M:%SZ'
    )
    report_update_timestamp = int(report_update_datetime.timestamp())
    return report_update_timestamp


def main():
    """
    При запуске бот запрашивает работы за все время. Последующие запросы отправляются
    с `timestamp`, равным `date_updated` последней работы.
    """
    check_tokens()
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0
    previous_report = {}
    previous_message = ''
    while True:
        try:
            check_tokens()
            response = get_api_answer(current_timestamp)
            current_report = check_response(response)[0]
            if previous_report != current_report:
                message = parse_status(current_report)
                logger.info('Изменился статус работы')
                send_message(bot, message)
                previous_report = current_report.copy()
                current_timestamp = get_timestamp(current_report)
            else:
                logger.debug('Статус работы не изменился.')
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if message != previous_message:
                send_message(bot, message)
                previous_message = message
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
