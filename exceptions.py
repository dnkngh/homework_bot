class MissingTokenError(Exception):
    """Исключение возникает при отсутствии необходимых переменных окружения."""
    pass


class SendMessageError(Exception):
    """Исключение возникает при ошибках при отправке сообщений в Telegram."""
    pass


class HomeworkServiceError(Exception):
    """.
    Базовый класс исключений для ошибок, возникающих при взаимодействии с
    сервисом Практикум.Домашка. При возникновении ошибки необходимо отправить
    пользователю описание проблемы в Telegram и залогировать ее.
    """
    pass


class ResponseError(HomeworkServiceError):
    """.
    Исключение возникает в случае ошибок сервиса Практикум.Домашка (при получении
    кода != 200).
    """
    pass


class EndpointUnavailableError(HomeworkServiceError):
    """.
    Исключение возникает при недоступности сервиса Практикум.Домашка (код 404).
    """
    pass


class RequestError(HomeworkServiceError):
    """Исключение возникает при сбоях при запросе к сервису Практикум.Домашка."""
    pass


class WrongStatusError(HomeworkServiceError):
    """
    Исключение возникает в случае, если в ответе получен не предусмотренный
    словарем `UPDATE_MESSAGES` статус работы.
    """
    pass


