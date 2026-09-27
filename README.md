KittyBot

KittyBot — это Telegram-бот, который автоматически отслеживает статус проверки ваших домашних работ на платформе Практикум.

Бот каждые 10 минут опрашивает API Практикума и при изменении статуса проверки (например, если ревьюер взял работу на проверку или поставил зачёт) мгновенно отправляет уведомление в ваш Telegram. Если во время работы API возникает сбой или ошибка, бот оповещает о возникшей проблеме, избегая спама повторными сообщениями.
Так же бота

Бот использует следующие основные библиотеки (полный список доступен в requirements.txt):
- pyTelegramBotAPI (4.14.1) — библиотека для взаимодействия с Telegram Bot API.
- requests (2.26.0) — для выполнения HTTP-запросов к API.
- python-dotenv (0.20.0) — для загрузки переменных окружения из файла .env.
= flake8 (5.0.4) — линтер для проверки соответствия кода стандарту PEP 8.
- flake8-docstrings (1.6.0) — расширение flake8 для проверки наличия docstring-документации.
- pytest (7.1.3) — фреймворк для запуска автоматических тестов.
- pytest-timeout (2.1.0) — плагин pytest для контроля времени выполнения тестов.

Запуск проект:
1. Клонирование репозитория
git clone <URL_РЕПОЗИТОРИЯ>
cd homework_bot

2. Настройка виртуального окружения
Создайте и активируйте виртуальное окружение:

macOS / Linux:
python3 -m venv venv
source venv/bin/activate

Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1

3. Установка зависимостей
pip install -r requirements.txt


4. Настройка переменных окружения
Необходимо создать файл .env в корневой директории проекта и заполнить его своими данными:
PRACTICUM_TOKEN=ваш_токен_яндекс_практикума
TELEGRAM_TOKEN=ваш_токен_телеграм_бота
TELEGRAM_CHAT_ID=ваш_telegram_chat_id

Где взять токены?
PRACTICUM_TOKEN: Можно получить по адресу https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9f0e52db455f971312e3fa19346f.
TELEGRAM_TOKEN: Получите у официального бота @BotFather в Telegram при создании нового бота.
TELEGRAM_CHAT_ID: Узнайте свой ID с помощью бота @userinfobot или @myidbot.

5. Изменение ресурса подключения (опционально):
В случае, если нужно подключиться к другому ресурсу, нужно заменить URL API Практикума на целевой в файле homework.py:
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

6. Запуск бота
python homework.py

Автор: Панкратов Г.А.