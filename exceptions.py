class EndpointUnavailableError(Exception):
    """Эндпоинт API недоступен или вернул код, отличный от 200."""


class InvalidResponseFormatError(TypeError):
    """Ответ API не является словарем."""


class MissingTokenError(Exception):
    """Отсутствует одна из обязательных переменных окружения."""


class TelegramMessageSendError(Exception):
    """Ошибка отправки сообщения в Telegram."""
