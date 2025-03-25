# handlers_recipes.py
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from assistant import MENU, RECIPES
from config import DISHES
import lunch  # ваш lunch.py

logger = logging.getLogger(__name__)

async def recipes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик нажатий в разделе «Здоровые рецепты» (состояние RECIPES).
    """
    query = update.callback_query
    await query.answer()
    data = query.data

    # Кнопка «Назад» => вернуться в меню
    if data == 'start':
        from handlers_menu import start_menu
        return await start_menu(update, context)

    # Пример: «lunch» => показать категории обедов
    if data == "lunch":
        # Инициализация LunchGenerator при необходимости
        if "lunch_generator" not in context.user_data:
            try:
                lunch_generator = lunch.LunchGenerator(data_source=DISHES)
                context.user_data["lunch_generator"] = lunch_generator
                logger.info("LunchGenerator инициализирован.")
            except Exception as e:
                logger.error(f"Ошибка при загрузке LunchGenerator: {e}")
                await query.edit_message_text(
                    text=f"Ошибка при загрузке обедов: {e}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Назад", callback_data="start")]
                    ])
                )
                return RECIPES

        keyboard_categories = [
            [InlineKeyboardButton("Первые", callback_data="category_Первое блюдо")],
            [InlineKeyboardButton("Основные", callback_data="category_Основное блюдо")],
            [InlineKeyboardButton("Гарниры", callback_data="category_Гарниры")],
            [InlineKeyboardButton("Салаты", callback_data="category_Салаты")],
            [InlineKeyboardButton("Назад", callback_data="start")]
        ]
        await query.edit_message_text(
            text="Выберите категорию блюд обеда:",
            reply_markup=InlineKeyboardMarkup(keyboard_categories)
        )
        return RECIPES

    elif data.startswith("category_"):
        category = data.split("_", 1)[1]
        context.user_data["current_category"] = category

        lunch_generator = context.user_data.get("lunch_generator")
        if not lunch_generator:
            await query.edit_message_text(
                text="Ошибка: генератор обедов не инициализирован.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Назад", callback_data="start")]
                ])
            )
            return RECIPES

        dishes = lunch_generator.get_dishes_by_category(category)
        if not dishes:
            await query.edit_message_text(
                text=f"В категории {category} нет доступных блюд.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Назад", callback_data="lunch")]
                ])
            )
            return RECIPES

        # Формируем кнопки
        keyboard_dishes = []
        for i, dish in enumerate(dishes):
            keyboard_dishes.append([
                InlineKeyboardButton(dish, callback_data=f"dish_{i}")
            ])
        keyboard_dishes.append([InlineKeyboardButton("Назад", callback_data="lunch")])

        context.user_data["dish_mapping"] = {f"dish_{i}": dish for i, dish in enumerate(dishes)}

        await query.edit_message_text(
            text=f"Выберите блюдо из категории '{category}':",
            reply_markup=InlineKeyboardMarkup(keyboard_dishes)
        )
        return RECIPES

    elif data.startswith("dish_"):
        dish_key = data
        dish_name = context.user_data["dish_mapping"].get(dish_key)
        if not dish_name:
            await query.edit_message_text(
                text="Ошибка: блюдо не найдено.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Назад", callback_data=f"category_{context.user_data.get('current_category')}")]
                ])
            )
            return RECIPES

        context.user_data["selected_dish"] = dish_name

        # Меню: «Приготовление» или «Назад»
        keyboard_dish_actions = [
            [InlineKeyboardButton("Приготовление", callback_data="preparation")],
            [InlineKeyboardButton("Назад", callback_data=f"category_{context.user_data.get('current_category')}")]
        ]
        await query.edit_message_text(
            text=f"Вы выбрали: {dish_name}.",
            reply_markup=InlineKeyboardMarkup(keyboard_dish_actions)
        )
        return RECIPES

    elif data == "preparation":
        dish_name = context.user_data.get("selected_dish")
        lunch_generator = context.user_data.get("lunch_generator")

        if not dish_name or not lunch_generator:
            await query.edit_message_text(
                text="Ошибка: данные о блюде недоступны.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Назад", callback_data=f"category_{context.user_data.get('current_category')}")]
                ])
            )
            return RECIPES

        details = lunch_generator.get_dish_details(dish_name)
        await query.edit_message_text(
            text=details,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Назад", callback_data=f"category_{context.user_data.get('current_category')}")]
            ])
        )
        return RECIPES

    # Другие кнопки (завтраки, ужины, напитки) – сделайте аналогично:
    elif data in ("breakfast", "dinner", "drinks"):
        await query.edit_message_text(
            text=f"Пока что тут нет логики, но вы выбрали: {data}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Назад", callback_data="start")]
            ])
        )
        return RECIPES

    # Ничего не подошло – остаёмся в RECIPES
    return RECIPES
