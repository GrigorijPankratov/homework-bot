"""Telegram-бот для отслеживания статусов проверки домашних работ."""

import logging
import os
import sys
import time
from http import HTTPStatus

from dotenv import load_dotenv
import requests
import telebot

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
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
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
    logging.debug(f'Начало отправки сообщения в Telegram: "{message}"')
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except (
        telebot.apihelper.ApiException,
        requests.RequestException
    ) as error:
        raise TelegramMessageSendError(
            f'Сбой при отправке сообщения в Telegram: {error}'
        ) from error
    else:
        logging.debug(f'Удачная отправка сообщения в Telegram: "{message}"')


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


def send_message_if_new(bot, message, last_sent_message):
    """Отправка сообщение в Telegram, если оно отличается от предыдущего."""
    if message and message != last_sent_message:
        send_message(bot, message)
        return message
    return last_sent_message


def main():
    """Основная логика работы бота."""
    try:
        check_tokens()
    except MissingTokenError as error:
        logging.critical(f'{error}. Программа принудительно остановлена.')
        sys.exit(1)

    bot = telebot.TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_sent_message = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)

            if not homeworks:
                logging.debug('Отсутствие в ответе новых статусов.')
            else:
                message = parse_status(homeworks[0])
                last_sent_message = send_message_if_new(
                    bot, message, last_sent_message
                )

            timestamp = response.get('current_date', timestamp)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            try:
                last_sent_message = send_message_if_new(
                    bot, message, last_sent_message
                )
            except TelegramMessageSendError as send_error:
                logging.error(
                    f'Не удалось отправить сообщение об ошибке: {send_error}'
                )

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    main()
