# handlers_recipes.py

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from states import MENU, RECIPES
from config import DISHES
import lunch
import drinks
import breakfast  # Ваш модуль с классом BreakfastGenerator

logger = logging.getLogger(__name__)

async def recipes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # 1. Если пользователь нажал "start" или "back_to_menu"
    if data in ('start', 'back_to_menu'):
        from handlers_menu import start_menu
        return await start_menu(update, context)

    # 2. "Завтраки"
    elif data == "breakfast":
        # Инициализируем BreakfastGenerator при необходимости
        if "breakfast_generator" not in context.user_data:
            try:
                context.user_data["breakfast_generator"] = breakfast.BreakfastGenerator("Data/breakfast.csv")
                logger.info("BreakfastGenerator инициализирован.")
            except Exception as e:
                logger.error(f"Ошибка при загрузке завтраков: {e}")
                await query.edit_message_text(
                    text=f"Ошибка при загрузке завтраков: {e}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Назад", callback_data="start")]
                    ])
                )
                return RECIPES

        bf_gen = context.user_data["breakfast_generator"]
        categories = bf_gen.get_unique_categories("завтрак")  # «Блюдо из»

        if not categories:
            await query.edit_message_text(
                text="Не найдено ни одной категории для завтраков.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Назад", callback_data="start")]
                ])
            )
            return RECIPES

        # Формируем кнопки подкатегорий завтрака
        keyboard_cats = []
        for cat in categories:
            callback_data = f"break_cat_{cat}"
            keyboard_cats.append([InlineKeyboardButton(cat, callback_data=callback_data)])

        keyboard_cats.append([InlineKeyboardButton("Назад", callback_data="start")])
        await query.edit_message_text(
            text="Выберите категорию для завтрака:",
            reply_markup=InlineKeyboardMarkup(keyboard_cats)
        )
        context.user_data["current_meal_type"] = "завтрак"
        return RECIPES

    # 3. "Полдники"
    elif data == "poldnik":
        # Используем тот же файл breakfast.csv, но фильтруем по «полдник»
        if "breakfast_generator" not in context.user_data:
            try:
                context.user_data["breakfast_generator"] = breakfast.BreakfastGenerator("Data/breakfast.csv")
                logger.info("BreakfastGenerator инициализирован (полдники).")
            except Exception as e:
                logger.error(f"Ошибка при загрузке полдников: {e}")
                await query.edit_message_text(
                    text=f"Ошибка при загрузке полдников: {e}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Назад", callback_data="start")]
                    ])
                )
                return RECIPES

        bf_gen = context.user_data["breakfast_generator"]
        categories = bf_gen.get_unique_categories("полдник")

        if not categories:
            await query.edit_message_text(
                text="Не найдено ни одной категории для полдников.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Назад", callback_data="start")]
                ])
            )
            return RECIPES

        keyboard_cats = []
        for cat in categories:
            callback_data = f"pold_cat_{cat}"
            keyboard_cats.append([InlineKeyboardButton(cat, callback_data=callback_data)])

        keyboard_cats.append([InlineKeyboardButton("Назад", callback_data="start")])
        await query.edit_message_text(
            text="Выберите категорию для полдника:",
            reply_markup=InlineKeyboardMarkup(keyboard_cats)
        )
        context.user_data["current_meal_type"] = "полдник"
        return RECIPES

    # 4. Когда пользователь выбрал категорию завтрака
    elif data.startswith("break_cat_"):
        selected_cat = data.split("break_cat_")[1]
        bf_gen = context.user_data["breakfast_generator"]
        meal_type = "завтрак"

        items = bf_gen.get_items_by_category(meal_type, selected_cat)
        if not items:
            await query.edit_message_text(
                text=f"В категории «{selected_cat}» (завтрак) нет блюд.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Назад", callback_data="breakfast")]
                ])
            )
            return RECIPES

        # Формируем кнопки блюд
        keyboard_items = []
        for i, name in enumerate(items):
            callback_data = f"break_item_{i}"
            keyboard_items.append([InlineKeyboardButton(name, callback_data=callback_data)])

        context.user_data["breakfast_map"] = {f"break_item_{i}": n for i, n in enumerate(items)}
        context.user_data["breakfast_current_cat"] = selected_cat

        keyboard_items.append([InlineKeyboardButton("Назад", callback_data="breakfast")])
        await query.edit_message_text(
            text=f"Выберите блюдо из категории «{selected_cat}» (завтрак):",
            reply_markup=InlineKeyboardMarkup(keyboard_items)
        )
        return RECIPES

    elif data.startswith("break_item_"):
        bf_gen = context.user_data["breakfast_generator"]
        item_map = context.user_data.get("breakfast_map", {})
        item_key = data
        item_name = item_map.get(item_key)
        if not item_name:
            await query.edit_message_text(
                text="Блюдо не найдено (завтрак).",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Назад", callback_data="breakfast")]
                ])
            )
            return RECIPES

        details = bf_gen.get_item_details(item_name)
        selected_cat = context.user_data.get("breakfast_current_cat", "...")
        await query.edit_message_text(
            text=details,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Назад", callback_data=f"break_cat_{selected_cat}")]
            ])
        )
        return RECIPES

    # 5. Когда пользователь выбрал категорию полдника
    elif data.startswith("pold_cat_"):
        selected_cat = data.split("pold_cat_")[1]
        bf_gen = context.user_data["breakfast_generator"]
        meal_type = "полдник"

        items = bf_gen.get_items_by_category(meal_type, selected_cat)
        if not items:
            await query.edit_message_text(
                text=f"В категории «{selected_cat}» (полдник) нет блюд.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Назад", callback_data="poldnik")]
                ])
            )
            return RECIPES

        keyboard_items = []
        for i, name in enumerate(items):
            callback_data = f"pold_item_{i}"
            keyboard_items.append([InlineKeyboardButton(name, callback_data=callback_data)])

        context.user_data["poldnik_map"] = {f"pold_item_{i}": n for i, n in enumerate(items)}
        context.user_data["poldnik_current_cat"] = selected_cat

        keyboard_items.append([InlineKeyboardButton("Назад", callback_data="poldnik")])
        await query.edit_message_text(
            text=f"Выберите блюдо из категории «{selected_cat}» (полдник):",
            reply_markup=InlineKeyboardMarkup(keyboard_items)
        )
        return RECIPES

    elif data.startswith("pold_item_"):
        bf_gen = context.user_data["breakfast_generator"]
        item_map = context.user_data.get("poldnik_map", {})
        item_key = data
        item_name = item_map.get(item_key)
        if not item_name:
            await query.edit_message_text(
                text="Блюдо не найдено (полдник).",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Назад", callback_data="poldnik")]
                ])
            )
            return RECIPES

        details = bf_gen.get_item_details(item_name)
        selected_cat = context.user_data.get("poldnik_current_cat", "...")
        await query.edit_message_text(
            text=details,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Назад", callback_data=f"pold_cat_{selected_cat}")]
            ])
        )
        return RECIPES

    # 6. Логика для "lunch", "dinner" и "drinks" уже есть — оставим
    #    (Судя по вашему коду, она ниже)

    # --- Уже существующий блок "lunch" / "drinks" / "dinner" ---
    elif data == "lunch":
        # Если нужно
        pass

    # ----- или, если у вас уже есть блок drinks -----
    elif data == "drinks":
        # Инициализация DrinksGenerator
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
            keyboard_drinks_list.append([InlineKeyboardButton(drink_name, callback_data=f"drinks_name_{i}")])

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

    # Ничего не подошло:
    return RECIPES
