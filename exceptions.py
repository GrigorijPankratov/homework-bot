class EndpointUnavailableError(Exception):
    """Вызывается, если эндпоинт API недоступен или вернул код, отличный от 200."""


class InvalidResponseFormatError(TypeError):
    """Вызывается, если ответ API не является словарем."""


class MissingTokenError(Exception):
    """Вызывается, если отсутствует одна из обязательных переменных окружения."""


class TelegramMessageSendError(Exception):
    """Вызывается при ошибке отправки сообщения в Telegram."""