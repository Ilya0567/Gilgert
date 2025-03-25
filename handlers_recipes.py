import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from states import MENU, RECIPES
from config import DISHES
import lunch
import drinks  # Модуль drinks.py с классом DrinksGenerator

logger = logging.getLogger(__name__)

async def recipes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Если пользователь нажал "start" или "back_to_menu"
    if data in ('start', 'back_to_menu'):
        from handlers_menu import start_menu
        return await start_menu(update, context)

    # Если выбрал "завтраки", "обеды" или "ужины"
    elif data in ("breakfast", "lunch", "dinner"):
        if data == "lunch":
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
                [InlineKeyboardButton("Напитки", callback_data="drinks")],
                [InlineKeyboardButton("Назад", callback_data="start")]
            ]
            await query.edit_message_text(
                text="Выберите категорию блюд обеда:",
                reply_markup=InlineKeyboardMarkup(keyboard_categories)
            )
            return RECIPES

        elif data == "breakfast":
            keyboard_categories = [
                [InlineKeyboardButton("Какие-то категории завтрака", callback_data="category_Завтрак1")],
                [InlineKeyboardButton("Напитки", callback_data="drinks")],
                [InlineKeyboardButton("Назад", callback_data="start")]
            ]
            await query.edit_message_text(
                text="Выберите категорию блюд для завтрака:",
                reply_markup=InlineKeyboardMarkup(keyboard_categories)
            )
            return RECIPES

        elif data == "dinner":
            keyboard_categories = [
                [InlineKeyboardButton("Категория 1 (ужин)", callback_data="category_Ужин1")],
                [InlineKeyboardButton("Напитки", callback_data="drinks")],
                [InlineKeyboardButton("Назад", callback_data="start")]
            ]
            await query.edit_message_text(
                text="Выберите категорию блюд ужина:",
                reply_markup=InlineKeyboardMarkup(keyboard_categories)
            )
            return RECIPES

    # Работа с блюдами (category_...)
    elif data.startswith("category_"):
        category = data.split("_", 1)[1]
        logger.info(f"Пользователь выбрал категорию: {category}")

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
                text=f"В категории '{category}' нет доступных блюд.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Назад", callback_data="lunch")]
                ])
            )
            return RECIPES

        keyboard_dishes = []
        for i, dish in enumerate(dishes):
            keyboard_dishes.append([InlineKeyboardButton(dish, callback_data=f"dish_{i}")])
        keyboard_dishes.append([InlineKeyboardButton("Назад", callback_data="lunch")])

        context.user_data["dish_mapping"] = {f"dish_{i}": dish for i, dish in enumerate(dishes)}
        context.user_data["current_category"] = category  # чтобы вернуться назад правильно

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

    # ----- Работа с напитками -----
    elif data == "drinks":
        # При первом обращении - инициализируем DrinksGenerator
        if "drinks_generator" not in context.user_data:
            try:
                context.user_data["drinks_generator"] = drinks.DrinksGenerator("Data/drinks.csv")
                logger.info("DrinksGenerator инициализирован.")
            except Exception as e:
                logger.error(f"Ошибка при загрузке DrinksGenerator: {e}")
                await query.edit_message_text(
                    text=f"Ошибка при загрузке напитков: {e}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Назад", callback_data="start")]
                    ])
                )
                return RECIPES

        drinks_generator = context.user_data["drinks_generator"]
        categories = drinks_generator.get_unique_categories()

        if not categories:
            await query.edit_message_text(
                text="Напитков не найдено.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Назад", callback_data="start")]
                ])
            )
            return RECIPES

        keyboard_drinks_cats = []
        for cat in categories:
            callback = f"drinks_cat_{cat}"
            keyboard_drinks_cats.append([InlineKeyboardButton(cat, callback_data=callback)])

        keyboard_drinks_cats.append([InlineKeyboardButton("Назад", callback_data="start")])

        await query.edit_message_text(
            text="Выберите категорию напитков:",
            reply_markup=InlineKeyboardMarkup(keyboard_drinks_cats)
        )
        return RECIPES

    elif data.startswith("drinks_cat_"):
        selected_cat = data.split("drinks_cat_")[1]
        drinks_generator = context.user_data.get("drinks_generator")

        if not drinks_generator:
            await query.edit_message_text(
                text="Ошибка: нет данных по напиткам.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="drinks")]])
            )
            return RECIPES

        drinks_in_cat = drinks_generator.get_drinks_by_category(selected_cat)
        if not drinks_in_cat:
            await query.edit_message_text(
                text=f"В категории «{selected_cat}» нет напитков.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="drinks")]])
            )
            return RECIPES

        keyboard_drinks_list = []
        for i, drink_name in enumerate(drinks_in_cat):
            keyboard_drinks_list.append([
                InlineKeyboardButton(drink_name, callback_data=f"drinks_name_{i}")
            ])

        context.user_data["drinks_mapping"] = {f"drinks_name_{i}": dn for i, dn in enumerate(drinks_in_cat)}
        context.user_data["drinks_current_cat"] = selected_cat

        keyboard_drinks_list.append([InlineKeyboardButton("Назад", callback_data="drinks")])

        await query.edit_message_text(
            text=f"Выберите напиток из категории «{selected_cat}»:",
            reply_markup=InlineKeyboardMarkup(keyboard_drinks_list)
        )
        return RECIPES

    elif data.startswith("drinks_name_"):
        drinks_generator = context.user_data.get("drinks_generator")
        if not drinks_generator:
            await query.edit_message_text(
                text="Ошибка: нет данных по напиткам.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="drinks")]])
            )
            return RECIPES

        drink_key = data
        drink_name_map = context.user_data.get("drinks_mapping", {})
        drink_name = drink_name_map.get(drink_key)
        if not drink_name:
            await query.edit_message_text(
                text="Напиток не найден.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="drinks")]])
            )
            return RECIPES

        details = drinks_generator.get_drink_details(drink_name)
        await query.edit_message_text(
            text=details,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Назад", callback_data=f"drinks_cat_{context.user_data.get('drinks_current_cat')}")]
            ])
        )
        return RECIPES

    # Ничего не подошло
    return RECIPES
