from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes
from collections.abc import Mapping
import pandas as pd
import logging

from data_operation import save_user_data, check_product, id_request
from config import DATA_FILE, TOKEN_BOT, CHAT_ID

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция, которая будет вызвана при команде /start
async def start(update: Updater, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("О нас", callback_data='about')],
        [InlineKeyboardButton("У меня вопрос", callback_data='ask_question')],
        [InlineKeyboardButton("Проверить продукт", callback_data="check_product")]
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
    elif query.data == 'check_product':
        await query.edit_message_text(text="Пожалуйста, введите название продукта, который Вас интересует.")
        
        context.user_data['check_product'] = True

# Функция для обработки текстовых сообщений
async def handle_message(update: Updater, context: ContextTypes.DEFAULT_TYPE) -> None:
    # если пользователь задаёт вопрос
    if context.user_data.get('awaiting_question'): 
        # Если ожидается вопрос от пользователя
        timestamp = update.message.date.timestamp()
        question = update.message.text
        user_id = update.message.from_user.id
        user_name = update.message.from_user.username or update.message.from_user.full_name
        context.user_data['awaiting_question'] = False
        
        # Сохранение данных с новым вопросом
        question_id = save_user_data(timestamp, user_id, question, None)
        df = pd.read_csv(DATA_FILE, index_col=False)
        
        # отправляем уведомление
        logger.info("Уведомление отправляется в чат")
        await update.message.reply_text(
            f"- - - - - - - - - - - - - - - - - - - - - - -  Ваш вопрос:  - - - - - - - - - - - - - - - - - - - - - - -\n"
            f"{question}. \n"
            "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n"
            "Спасибо за обращение! Мы ответим вам в ближайшее время.")
        
        # перенаправление вопроса экспертам
        await context.bot.send_message(chat_id=CHAT_ID, 
                                       text=f'Сообщение №{question_id} от пользователя {user_name}:\n{question}')
    # если пользователь проверяет продукт
    elif context.user_data.get('check_product'): 
        timestamp = update.message.date.timestamp()
        product = update.message.text
        user_id = update.message.from_user.id
        user_name = update.message.from_user.username or update.message.from_user.full_name
        context.user_data['check_product'] = False
        # ищем ответ 
        answer = check_product(product)
        # отвечаем пользователю
        await update.message.reply_text(answer)
        # если требуется, перенаправляем вопрос специалистам
        if len(answer.split(".")) > 2: # так как в ответе, где требуется помощь специалиста 2 предложения
            id_product_question = id_request()
            await context.bot.send_message(chat_id=CHAT_ID, 
                                       text=f'Вопрос по продукту №{id_product_question} от пользователя {user_name}:\n{product}')
    else:
        # Проверка типа чата, чтобы бот отвечал только в личных сообщениях
        if update.message.chat.type == 'private':
            await update.message.reply_text("Пожалуйста, используйте кнопки для взаимодействия со мной.")

    



# Главная функция для запуска бота
def main():
    # Создаем приложение
    application = ApplicationBuilder().token(TOKEN_BOT).build()

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