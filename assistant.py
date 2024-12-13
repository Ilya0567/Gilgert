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

# Глобальная переменная для хранения выбранного блюда
CURRENT_DISH = {}

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

# Обработчик нажатий на кнопки
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
        reply_markup = InlineKeyboardMarkup(keyboard_recipes)
        await query.edit_message_text("Выберите категорию здоровых рецептов:", reply_markup=reply_markup)

    # Обработчик нажатия кнопки "Обед"
    if query.data == "lunch":
        if "lunch_generator" not in context.user_data:
            try:
                lunch_ = lunch.LunchGenerator(data_source=DISHES)
                context.user_data["lunch_generator"] = lunch_
                context.user_data["lunch_dishes"] = lunch_.lunch  # Сохраняем текущий обед
            except Exception as e:
                await query.edit_message_text(f"Произошла ошибка при загрузке обеда: {str(e)}")
                return

        dishes = context.user_data["lunch_dishes"]
        keyboard_dishes = [
            [InlineKeyboardButton(f"{dish}", callback_data=f"dish_{category}")] for category, dish in dishes.items() if dish
        ]
        keyboard_dishes.append([InlineKeyboardButton("Назад", callback_data="healthy_recipes")])
        reply_markup = InlineKeyboardMarkup(keyboard_dishes)
        await query.edit_message_text(
            text="Выберите одно из блюд на обед:",
            reply_markup=reply_markup
        )

    # Логика при выборе блюда
    if query.data.startswith("dish_"):
        category = query.data.split("_")[1]
        CURRENT_DISH[query.from_user.id] = category
        keyboard_dish_options = [
            [InlineKeyboardButton("Приготовление", callback_data=f"preparation_{category}")],
            [InlineKeyboardButton("Изменить", callback_data=f"change_{category}")],
            [InlineKeyboardButton("Назад", callback_data="lunch")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard_dish_options)
        await query.edit_message_text(
            text=f"Вы выбрали блюдо: {context.user_data['lunch_dishes'][category]}. Что вы хотите сделать?",
            reply_markup=reply_markup
        )

    # Логика для изменения блюда
    if query.data.startswith("change_"):
        category = query.data.split("_")[1]
        lunch_generator = context.user_data["lunch_generator"]
        new_dish = lunch_generator.change_dish(category)
        context.user_data["lunch_dishes"][category] = new_dish

        keyboard_dish_options = [
            [InlineKeyboardButton("Приготовление", callback_data=f"preparation_{category}")],
            [InlineKeyboardButton("Изменить", callback_data=f"change_{category}")],
            [InlineKeyboardButton("Назад", callback_data="lunch")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard_dish_options)
        await query.edit_message_text(
            text=f"Блюдо категории '{category}' изменено. Новое блюдо: {new_dish}.",
            reply_markup=reply_markup
        )

    # Логика для отображения ингредиентов и способа приготовления
    if query.data.startswith("preparation_"):
        category = query.data.split("_")[1]
        
        # Получаем текущее выбранное блюдо
        if "lunch_dishes" in context.user_data and category in context.user_data["lunch_dishes"]:
            selected_dish = context.user_data["lunch_dishes"][category]
            lunch_generator = context.user_data["lunch_generator"]
            
            # Получаем актуальные детали для нового блюда
            details = lunch_generator.get_dish_details(selected_dish)
            
            # Отправляем пользователю детали
            await query.edit_message_text(
                text=f"{details}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data=f"dish_{category}")]])
            )
        else:
            # Обработка ошибок, если данные блюда отсутствуют
            await query.edit_message_text(
                text="Ошибка: Не удалось найти выбранное блюдо. Попробуйте заново.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="lunch")]])
            )



    # Логика для изменения блюда
    if query.data.startswith("change_"):
        category = query.data.split("_")[1]
        lunch_generator = context.user_data["lunch_generator"]
        new_dish = lunch_generator.change_dish(category)
        context.user_data["lunch_dishes"][category] = new_dish

        keyboard_dish_options = [
            [InlineKeyboardButton("Ингредиенты", callback_data=f"ingredients_{category}")],
            [InlineKeyboardButton("Изменить", callback_data=f"change_{category}")],
            [InlineKeyboardButton("Назад", callback_data="lunch")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard_dish_options)
        await query.edit_message_text(
            text=f"Блюдо категории '{category}' изменено. Новое блюдо: {new_dish}.",
            reply_markup=reply_markup
        )

    # Логика для отображения ингредиентов
    if query.data.startswith("ingredients_"):
        category = query.data.split("_")[1]
        selected_dish = context.user_data["lunch_dishes"][category]
        lunch_generator = context.user_data["lunch_generator"]
        ingredients = lunch_generator.get_ingredients()

        await query.edit_message_text(
            text=f"Ингредиенты для блюда '{selected_dish}':\n\n{ingredients}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data=f"dish_{category}")]])
        )

        
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
