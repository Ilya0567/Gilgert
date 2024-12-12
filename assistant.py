from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes
from collections.abc import Mapping
import pandas as pd
import logging

from data_operation import save_user_data, check_product, id_request
import lunch
from config import DATA_FILE, TOKEN_BOT, CHAT_ID, DISHES

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция, которая будет вызвана при команде /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("О нас", callback_data='about')],
        [InlineKeyboardButton("У меня вопрос", callback_data='ask_question')],
        [InlineKeyboardButton("Проверить продукт", callback_data="check_product")],
        [InlineKeyboardButton("Здоровые рецепты", callback_data="healthy_recipes")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(
            text="👋 Привет! Я ваш помощник, созданный специально для помощи людям с синдромом Жильбера.\n\n"
            "Я могу помочь Вам с рекомендациями по продуктам питания. Пожалуйста, используйте кнопку ниже, чтобы узнать, можно ли есть определенный продукт. Также Вы можете посмотреть собранные мной вкусные здоровые рецепты.\n\n"
            "✨ Нажмите на кнопку 'Проверить продукт', чтобы начать.", 
            reply_markup=reply_markup
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            text="👋 Привет! Я ваш помощник, созданный специально для помощи людям с синдромом Жильбера.\n\n"
            "Я могу помочь Вам с рекомендациями по продуктам питания. Пожалуйста, используйте кнопку ниже, чтобы узнать, можно ли есть определенный продукт. Также Вы можете посмотреть собранные мной вкусные здоровые рецепты.\n\n"
            "✨ Нажмите на кнопку 'Проверить продукт', чтобы начать.", 
            reply_markup=reply_markup
        )

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

    # кнопки с категориями рецептов
    keyboard_recipes = [
            [InlineKeyboardButton("Завтраки", callback_data="breakfast")],
            [InlineKeyboardButton("Обеды", callback_data="lunch")],
            [InlineKeyboardButton("Ужины", callback_data="dinner")],
            [InlineKeyboardButton("Напитки", callback_data="drinks")],
            [InlineKeyboardButton("Назад", callback_data="start")]
        ]
    
    if query.data == "healthy_recipes":
        # Если нажали на кнопку "Здоровые рецепты", показываем дополнительные опции
        reply_markup = InlineKeyboardMarkup(keyboard_recipes)
        await query.edit_message_text("Выберите категорию здоровых рецептов:", reply_markup=reply_markup)



    # Обработчик нажатия кнопки "Обед"
    if query.data == "lunch":
        try:
            # Создаем объект LunchGenerator
            lunch_ = lunch.LunchGenerator(data_source=DISHES)
            dishes = lunch_.get_lunch_names()
            dishes_text = "\n".join([f"- {dish}" for dish in dishes])
            keyboard_dish_options = [
                [InlineKeyboardButton("Ингредиенты", callback_data="ingredients_lunch")],
                [InlineKeyboardButton("Изменить", callback_data="change_lunch")],
                [InlineKeyboardButton("Назад", callback_data="healthy_recipes")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard_dish_options)
            await query.edit_message_text(
                text=f"Вот список блюд на обед:\n\n{dishes_text}",
                reply_markup=reply_markup
            )
        except Exception as e:
            await query.edit_message_text(f"Произошла ошибка при загрузке обеда: {str(e)}")

    # # Обработчик кнопки "Ингредиенты"
    # if query.data == "ingredients_breakfast":
    #     dish = "Овсянка с фруктами"  # Здесь можно предусмотреть выбор конкретного блюда пользователем
    #     ingredients = recipe_manager.get_ingredients(dish)
    #     keyboard_ingredients_options = [
    #         [InlineKeyboardButton("Способ приготовления", callback_data="recipe_method")],
    #         [InlineKeyboardButton("Назад", callback_data="breakfast")],
    #         [InlineKeyboardButton("Главное меню", callback_data="start")]
    #     ]
    #     reply_markup = InlineKeyboardMarkup(keyboard_ingredients_options)
    #     await query.edit_message_text(
    #         text=f"Ингредиенты для блюда '{dish}':\n\n{ingredients}",
    #         reply_markup=reply_markup
    #     )

    # # Обработчик кнопки "Изменить"
    # if query.data == "change_breakfast":
    #     # Повторный вызов скрипта для выбора новых блюд (эмулируется повторным получением списка блюд)
    #     dishes = recipe_manager.get_dishes("breakfast")
    #     dishes_text = "\n".join([f"- {dish}" for dish in dishes])
    #     keyboard_dish_options = [
    #         [InlineKeyboardButton("Ингредиенты", callback_data="ingredients_breakfast")],
    #         [InlineKeyboardButton("Изменить", callback_data="change_breakfast")],
    #         [InlineKeyboardButton("Назад", callback_data="healthy_recipes")]
    #     ]
    #     reply_markup = InlineKeyboardMarkup(keyboard_dish_options)
    #     await query.edit_message_text(
    #         text=f"Обновленный список блюд на завтрак:\n\n{dishes_text}",
    #         reply_markup=reply_markup
    #     )

    # # Обработчик кнопки "Способ приготовления"
    # if query.data == "recipe_method":
    #     method = "1. Залейте овсянку горячей водой.\n2. Добавьте нарезанные фрукты и мед.\n3. Хорошо перемешайте."
    #     keyboard_method_options = [
    #         [InlineKeyboardButton("Назад", callback_data="ingredients_breakfast")],
    #         [InlineKeyboardButton("Главное меню", callback_data="start")]
    #     ]
    #     reply_markup = InlineKeyboardMarkup(keyboard_method_options)
    #     await query.edit_message_text(
    #         text=f"Способ приготовления:\n\n{method}",
    #         reply_markup=reply_markup
    #     )
        
    if query.data == "start":
        await update.callback_query.edit_message_text(
            text="👋 Привет! Я ваш помощник, созданный специально для помощи людям с синдромом Жильбера.\n\n"
            "Я могу помочь Вам с рекомендациями по продуктам питания. Пожалуйста, используйте кнопку ниже, чтобы узнать, можно ли есть определенный продукт. Также Вы можете посмотреть собранные мной вкусные здоровые рецепты.\n\n"
            "✨ Нажмите на кнопку 'Проверить продукт', чтобы начать.", 
            reply_markup=reply_markup)
    

    
      



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
        "✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨\n"
        "📩 *Ваш вопрос* 📩\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"❓ {question} ❓\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🙏 Спасибо за обращение! Мы ответим вам в ближайшее время.\n"
        "✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨",
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
        context.user_data['check_product'] = True
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
            await update.message.reply_text("👉 По5555жалуйста, используйте кнопки для взаимодействия со мной. 😊")


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
