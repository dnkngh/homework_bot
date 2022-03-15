import logging
import os
import sys
import time
from datetime import datetime
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telegram import Bot

from exceptions import (
    EndpointUnavailableError, HomeworkServiceError, MissingTokenError,
    ResponseError, RequestError, SendMessageError, WrongStatusError
)

logger = logging.getLogger(__name__)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/aa'

APPROVED = 'approved'
REVIEWVING = 'reviewing'
REJECTED = 'rejected'
TELEGRAM_MESSAGES = {
    APPROVED: 'Работа проверена: ревьюеру всё понравилось. Ура!',
    REVIEWVING: 'Работа взята на проверку ревьюером.',
    REJECTED: 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение `message` в указанный telegram-чат."""
    try:
        logger.info('Попытка отправить сообщение в Telegram отправлено.')
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение в Telegram успешно отправлено.')
    except Exception:
        raise SendMessageError('Не удалось отправить сообщение в Telegram.')


def get_api_answer(current_timestamp):
    """.
    Запрос к `API Yandex Practicum` с указанной временной меткой.
    В случае успешного запроса возвращает ответ API, приведенный к типам
    данных Python.
    """
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=headers,
            params=params
        )

        if homework_statuses.status_code == HTTPStatus.NOT_FOUND:
            raise EndpointUnavailableError(
                'Эндпоинт Практикум.Домашка недоступен. Код ответа: 404.'
            )

        if homework_statuses.status_code != HTTPStatus.OK:
            raise ResponseError(
                f'При запросе к сервису Практикум.Домашка возникла ошибка.'
                f'Код ответа: {homework_statuses.status_code}.'
            )

        return homework_statuses.json()

    except requests.exceptions.RequestException as error:
        raise RequestError(
            f'Сбой при запросе к сервису Практикум.Домашка: {error}.'
        )


def check_response(response):
    """.
    Проверка ответа API на корректность. При успешной проверке возвращает
    список домашних работ, доступный в ответе по ключу `homeworks`.
    """
    if not isinstance(response, dict):
        raise TypeError(
            f'Ответ сервиса не является словарем. Ответ сервиса {response}.'
        )

    if not response.get('current_date'):
        raise KeyError('В полученном ответе отсутствует ключ `current_date`.')

    if not response.get('homeworks'):
        raise KeyError('В полученном ответе отсутствует ключ `homeworks`.')

    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError(
            f'Значение по ключу `homeworks` не является списком.'
            f'Ответ сервиса: {homeworks}'
        )

    if not homeworks:
        raise IndexError('Значение по ключу `homeworks` - пустой список.')

    return homeworks


def parse_status(homework):
    """.
    Функция извлекает статус работы из ответа Яндекс.Практикум и возвращает
    готовую строку для отправки пользователю.
    """
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if not (homework_status and homework_name):
        raise KeyError(
            'В ответе отсутствуют ключи `homework_name` и/или `status`'
        )

    if homework_status not in TELEGRAM_MESSAGES:
        raise WrongStatusError('Получен некорректный статус работы.')

    verdict = TELEGRAM_MESSAGES.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности необходимых переменных окружения."""
    tokens_exist = PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID
    if tokens_exist:
        return tokens_exist
    return False


def get_timestamp(report) -> int:
    """.
    Функция в качестве параметра получает работу и возвращает время
    последнего изменения статуса этой работы в формате Unix time.
    """
    report_update_date = report.get('date_updated')
    report_update_datetime = datetime.strptime(
        report_update_date, '%Y-%m-%dT%H:%M:%SZ'
    )
    report_update_timestamp = int(report_update_datetime.timestamp())
    return report_update_timestamp


def main():
    """.
    При запуске бот запрашивает работы за все время. Последующие запросы
    отправляются с `timestamp`, равным `date_updated` последней работы.
    """
    if not check_tokens():
        logger.critical(MissingTokenError('Отсутствуют переменные окружения'))
        sys.exit('Отсутствуют переменные окружения')
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0
    previous_report = {}
    previous_message = ''
    while True:
        try:
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
        except HomeworkServiceError as error:
            logger.error(error)
            message = f'Сбой в работе программы: {error}'
            if message != previous_message:
                send_message(bot, message)
                previous_message = message
        except SendMessageError as error:
            logger.error(error)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler(stream=sys.stderr)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)

    main()
