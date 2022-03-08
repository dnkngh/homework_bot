class MissingTokenError(Exception):
    """Исключение возникает при отсутствии необходимых переменных окружения."""
    def __init__(self):
        self.message = 'Отсутствуют необходимые переменные окружения'
        super().__init__(self.message)


class EndpointUnavailableError(Exception):
    """Исключение возникает при недоступности сервиса Практикум.Домашка."""
    def __init__(self):
        self.message = 'Эндпоинт Практикум.Домашка недоступен.'
        super().__init__(self.message)


class RequestError(Exception):
    """Исключение возникает при сбоях при запросе к сервису Практикум.Домашка."""
    def __init__(self):
        self.message = (
            'При запросе к сервису Практикум.Домашка созникла ошибка.'
        )
        super().__init__(self.message)


class SendMessageFailureError(Exception):
    """Исключение возникает при ошибках при отправке сообщений в Telegram."""
    def __init__(self):
        self.message = 'Не удалось отпрвить сообщение в Telegram.'
        super().__init__(self.message)


class WrongStatusError(Exception):
    def __init__(self):
        self.message = 'Получен некорректный статус работы.'
        super().__init__(self.message)


class EmptyResponseError(Exception):
    """Исключение возникает при получении в ответе пустого словаря `homeworks`."""
    def __init__(self):
        self.message = 'Получен пустой словарь `homeworks`.'
        super().__init__(self.message)
