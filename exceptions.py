class MissingTokenError(Exception):
    """Исключение возникает при отсутствии необходимых переменных окружения."""
    pass


class ResponseError(Exception):
    """.
    Исключение возникает в случае ошибок сервиса Практикум.Домашка (при получении
    кода != 200).
    """
    pass


class EndpointUnavailableError(ResponseError):
    """.
    Исключение возникает при недоступности сервиса Практикум.Домашка (код 404).
    """
    pass


class RequestError(Exception):
    """Исключение возникает при сбоях при запросе к сервису Практикум.Домашка."""
    pass


class SendMessageError(Exception):
    """Исключение возникает при ошибках при отправке сообщений в Telegram."""
    pass


class WrongStatusError(Exception):
    """
    Исключение возникает в случае, если в ответе получен не предусмотренный
    словарем `UPDATE_MESSAGES` статус работы.
    """
    pass
