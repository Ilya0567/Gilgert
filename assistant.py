from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes
from collections.abc import Mapping
import datetime
import json
import os


# Имя файла для хранения данных вопросов
DATA_FILE = "data/questions.json"

# Функция для загрузки данных из JSON-файла
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    return {}

# Функция для сохранения данных в JSON-файл
def save_data(new_data):
    data = load_data()  # Загружаем существующие данные
    for user_id, user_data in new_data.items():
        if user_id in data:
            data[user_id]["questions"].extend(user_data["questions"])
        else:
            data[user_id] = user_data
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)


# Функция, которая будет вызвана при команде /start
async def start(update: Updater, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Расскажи о себе", callback_data='about')],
        [InlineKeyboardButton("У меня вопрос", callback_data='ask_question')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Добро пожаловать! Выберите действие:', reply_markup=reply_markup)


# Функция для обработки нажатий на кнопки
async def button(update: Updater, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'about':
        about_text = (
            "Мы молодая команда студентов из МФТИ, создающая ИИ-ассистента для людей с синдромом Жильбера. "
            "Наш бот предназначен для помощи и поддержки людей с этим заболеванием. "
            "На данном этапе мы внедряем первые функции, и в скором времени планируем добавить ИИ для улучшения возможностей бота. "
        )
        await query.edit_message_text(text= about_text)
    elif query.data == 'ask_question':
        await query.edit_message_text(text="Пожалуйста, задайте свой вопрос.")
        context.user_data['awaiting_question'] = True

# Функция для обработки текстовых сообщений
async def handle_message(update: Updater, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('awaiting_question'):
         # Если ожидается вопрос от пользователя
        question = update.message.text
        user_id = update.message.from_user.id
        user_name = update.message.from_user.username or update.message.from_user.full_name
        context.user_data['awaiting_question'] = False

        # Загрузка существующих данных
        data = load_data()
        if user_id not in data:
            data[user_id] = {"user_name": user_name, "questions": []}
        data[user_id]["questions"].append(question)
        # Сохранение данных с новым вопросом
        save_data(data)
        await update.message.reply_text(f"Вы задали вопрос: \n {question}. \n\nСпасибо за обращение! Мы ответим вам в ближайшее время.")
    else:
        await update.message.reply_text("Пожалуйста, используйте кнопки для взаимодействия со мной.")

# Главная функция для запуска бота
def main():
    # Вставьте ваш API-токен здесь
    TOKEN = '7497408437:AAHcpnlNUDAu2CpW1khxf5keiBmxXRWCjAY'

    # Создаем приложение
    application = ApplicationBuilder().token(TOKEN).build()

    # Регистрируем обработчик для команды /start
    application.add_handler(CommandHandler("start", start))

    # Регистрируем обработчик для нажатий на кнопки
    application.add_handler(CallbackQueryHandler(button))

    # Регистрируем обработчик для текстовых сообщений
    application.add_handler(MessageHandler(None, handle_message))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()