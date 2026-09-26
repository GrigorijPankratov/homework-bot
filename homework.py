import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telebot
from dotenv import load_dotenv

from exceptions import (
    EndpointUnavailableError,
    InvalidResponseFormatError,
    MissingTokenError,
    TelegramMessageSendError,
)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка доступности переменных окружения."""
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    missing_tokens = [name for name, value in tokens.items() if not value]
    if missing_tokens:
        missing_str = ', '.join(missing_tokens)
        raise MissingTokenError(
            f'Отсутствует обязательная переменная окружения: {missing_str}'
        )


def send_message(bot, message):
    """Отправка сообщения в Telegram."""
    try:
        logging.debug(f'Начало отправки сообщения в Telegram: "{message}"')
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f'Удачная отправка сообщения в Telegram: "{message}"')
    except Exception as error:
        raise TelegramMessageSendError(
            f'Сбой при отправке сообщения в Telegram: {error}'
        ) from error


def get_api_answer(timestamp):
    """Запрос к эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as error:
        raise EndpointUnavailableError(
            f'Сбой при запросе к эндпоинту {ENDPOINT}: {error}'
        ) from error

    if response.status_code != HTTPStatus.OK:
        raise EndpointUnavailableError(
            f'Эндпоинт {ENDPOINT} недоступен. Код ответа API: '
            f'{response.status_code}'
        )

    try:
        return response.json()
    except ValueError as error:
        raise InvalidResponseFormatError(
            f'Ответ сервера не может быть преобразован в JSON: {error}'
        ) from error


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API должен быть словарем.')

    if 'homeworks' not in response:
        raise KeyError('В ответе API отсутствует ключ "homeworks".')

    if 'current_date' not in response:
        raise KeyError('В ответе API отсутствует ключ "current_date".')

    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Значение ключа "homeworks" должно быть списком.')

    return homeworks


def parse_status(homework):
    """Извлечение из информации о данной домашней работе её статуса."""
    if 'homework_name' not in homework:
        raise KeyError(
            'В словаре домашней работы отсутствует ключ "homework_name".'
        )

    if 'status' not in homework:
        raise KeyError('В словаре домашней работы отсутствует ключ "status".')

    homework_name = homework.get('homework_name')
    status = homework.get('status')

    if status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Неожиданный статус домашней работы: {status}')

    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    try:
        check_tokens()
    except MissingTokenError as error:
        logging.critical(f'{error}. Программа принудительно остановлена.')
        sys.exit(1)

    bot = telebot.TeleBot(token=TELEGRAM_TOKEN)
    # Отладка
    timestamp = int(time.time())
    last_error_message = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)

            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)
            else:
                logging.debug('Отсутствие в ответе новых статусов.')

            timestamp = response.get('current_date', timestamp)
            last_error_message = ''

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)

            if message != last_error_message:
                try:
                    send_message(bot, message)
                    last_error_message = message
                except TelegramMessageSendError as send_error:
                    logging.error(
                        'Не удалось отправить сообщение об ошибке: '
                        f'{send_error}'
                    )

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    main()
