from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes
from collections.abc import Mapping
import pandas as pd


# Имя файла для хранения данных вопросов
DATA_FILE = "Data/questions.csv"
TOKEN_BOT = "7497408437:AAHcpnlNUDAu2CpW1khxf5keiBmxXRWCjAY"
CHAT_ID = "https://t.me/IlyaBetsukeli"


# Функция для отправки уведомления в личный чат
def send_notification(bot_token, chat_id, message):
    updater = Updater(token=bot_token)
    updater.bot.send_message(chat_id=chat_id, text=message)
    # Отправляем уведомление в собственный чат
    send_notification(bot_token, chat_id, f'New message from user {message}')
    
    

# функция для сохранения вопросов от пользователей
def save_user_data(timestamp, username, question, answer):
    # открываем файл с данными
    user_data = pd.read_csv(DATA_FILE, index_col=False)
    # создаем новый датафрейм
    new_entry = pd.DataFrame([{
        "timestamp": timestamp, 
        "username": username,
        "question": question,    
        "answer": answer
    }])
    
    # соединяем датасеты
    user_data = pd.concat([user_data, new_entry], ignore_index=True)
    # и сохраняем
    user_data.to_csv(DATA_FILE, index=False)
    
    # send_notification(TOKEN_BOT, CHAT_ID, new_entry)



# Функция, которая будет вызвана при команде /start
async def start(update: Updater, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("О нас", callback_data='about')],
        [InlineKeyboardButton("У меня вопрос", callback_data='ask_question')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Добро пожаловать!', reply_markup=reply_markup)


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
        timestamp = update.message.date.timestamp()
        question = update.message.text
        user_id = update.message.from_user.id
        user_name = update.message.from_user.username or update.message.from_user.full_name
        context.user_data['awaiting_question'] = False
        # Сохранение данных с новым вопросом
        save_user_data(timestamp, user_id, question, None)
        df = pd.read_csv(DATA_FILE, index_col=False)
        await update.message.reply_text(f"-------- Вы задали вопрос: --------\n {question}. "
                                        "------------------------------------ "
                                        "Спасибо за обращение! Мы ответим вам в ближайшее время.")
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