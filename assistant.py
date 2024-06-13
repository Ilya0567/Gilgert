from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("О нас", callback_data='about')],
        [InlineKeyboardButton("У меня вопрос", callback_data='ask_question')],
        [InlineKeyboardButton("Проверить продукт", callback_data="check_product")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Привет! Я ваш помощник, созданный специально для помощи людям с синдромом Жильбера.\n\n"
    "Я могу помочь Вам с рекомендациями по продуктам питания. Пожалуйста, используйте кнопку ниже, чтобы узнать, можно ли есть определенный продукт.\n\n"
    "✨ Нажмите на кнопку 'Проверить продукт', чтобы начать.", reply_markup=reply_markup)


# Функция для обработки нажатий на кнопки
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    main_menu_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Главное меню", callback_data='start')]
    ])

    if query.data == 'about':
        about_text = (
            "👩‍💻 Мы молодая команда студентов из МФТИ, создающая ИИ-ассистента для людей с синдромом Жильбера.\n\n"
            "🤖 Наш бот предназначен для помощи и поддержки людей с этим заболеванием.\n\n"
            "🚀 На данном этапе мы внедряем первые функции, и в скором времени планируем добавить ИИ для улучшения возможностей бота."
        )
        await query.edit_message_text(text=about_text, reply_markup=main_menu_keyboard)
    elif query.data == 'ask_question':
        await query.edit_message_text(text="❓ Пожалуйста, задайте свой вопрос.", reply_markup=main_menu_keyboard)
        context.user_data['awaiting_question'] = True
    elif query.data == 'check_product':
        await query.edit_message_text(text="🔍 Пожалуйста, введите название продукта, который Вас интересует.", reply_markup=main_menu_keyboard)
        context.user_data['check_product'] = True
    elif query.data == 'start':
        await start(update, context)

# Функция для обработки текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    main_menu_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Главное меню", callback_data='start')]
    ])

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
        "✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨\n"
        "📩 *Ваш вопрос* 📩\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"❓ {question} ❓\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🙏 Спасибо за обращение! Мы ответим вам в ближайшее время.\n"
        "✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨",
        parse_mode='Markdown', reply_markup=main_menu_keyboard
    )
        
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
        await update.message.reply_text(answer, reply_markup=main_menu_keyboard)
        # если требуется, перенаправляем вопрос специалистам
        if "ответ" in answer: 
            id_product_question = id_request()
            await context.bot.send_message(chat_id=CHAT_ID, 
                                       text=f'Вопрос по продукту №{id_product_question} от пользователя {user_name}:\n "{product}"')
    else:
        # Проверка типа чата, чтобы бот отвечал только в личных сообщениях
        if update.message.chat.type == 'private':
            await update.message.reply_text("👉 Пожалуйста, используйте кнопки для взаимодействия со мной. 😊")


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
