"""Здесь находятся константы"""

# Пути к файлам данных
DATA_FILE = "Data/questions.csv"
PRODUCT_PATH = "Data/Продукты.csv"
DISHES = "Data/Обеды_с_эмодзи_в_начале.csv"

# API ключи
OPENAI_API_KEY = "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"
TOKEN_BOT = "7497408437:AAHcpnlNUDAu2CpW1khxf5keiBmxXRWCjAY"
TELEGRAM_TOKEN = TOKEN_BOT  # Для совместимости с новым кодом

# ID чатов и пользователей
CHAT_ID = "-1002051079352"
# CHAT_ID = '669201758'

# Список ID администраторов (строки)
ADMIN_IDS = [
    "669201758",  # @betsu
]

# Настройки webhook для работы без перезапуска
WEBHOOK_URL = "https://your-domain.com"  # Замените на ваш домен
WEBHOOK_PORT = 8443  # Стандартный порт для webhook
WEBHOOK_PATH = f"/bot{TOKEN_BOT}"  # Путь для webhook

# Новые настройки из обновленного кода
ALLOWED_USER_IDS = []  # Пустой список = разрешены все пользователи
APP_ENV = "production"  # или "development"
DEBUG = False
SUPPORT_CHAT_ID = CHAT_ID  # Используем то же ID чата для поддержки
CONFIG_JSON_PATH = "config.json"  # Путь к файлу конфигурации

# Для запуска в режиме webhook используйте:
# python assistant.py --webhook
