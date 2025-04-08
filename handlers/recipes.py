# handlers_recipes.py

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from utils.states import MENU, RECIPES
from utils.config import DISHES
from meals import lunch
from meals import drinks
from meals import breakfast    # ваш класс BreakfastGenerator
from meals import poldnik      # ваш класс PoldnikGenerator

# Added imports
from database.database import SessionLocal # Assuming SessionLocal is here
from database.crud import add_recipe_rating # Assuming function to add rating is here
from database.models import ActionType # Import ActionType for tracking
from handlers.menu import start_menu

logger = logging.getLogger(__name__)

async def recipes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user # Get user info

    # Если пользователь нажал "start" или "back_to_menu"
    if data in ('start', 'back_to_menu'):
        return await start_menu(update, context)

    # ---------- Завтраки ----------
    elif data == "breakfast":
        # При первом обращении - инициализируем BreakfastGenerator
        if "breakfast_generator" not in context.user_data:
            try:
                # Предположим, у вас CSV "Data/breakfast.csv"
                # и класс BreakfastGenerator
                context.user_data["breakfast_generator"] = breakfast.BreakfastGenerator("Data/breakfast.csv")
                logger.info("BreakfastGenerator инициализирован для завтраков.")
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
        # Получаем список категорий (например, 'каша', 'бутерброд', и т.д.)
        categories = bf_gen.get_unique_categories()

        if not categories:
            await query.edit_message_text(
                text="Не найдено ни одной категории для завтраков.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Назад", callback_data="start")]
                ])
            )
            return RECIPES

        # Формируем кнопки для категорий (столбец 'Блюдо из')
        keyboard_cats = []
        for cat in categories:
            callback_data = f"bcat_{cat}"
            keyboard_cats.append([InlineKeyboardButton(cat, callback_data=callback_data)])

        # Кнопка назад
        keyboard_cats.append([InlineKeyboardButton("Назад", callback_data="start")])

        await query.edit_message_text(
            text="Выберите категорию блюд (завтрак):",
            reply_markup=InlineKeyboardMarkup(keyboard_cats)
        )
        return RECIPES

    elif data.startswith("bcat_"):
        # Пользователь выбрал конкретную категорию завтраков
        selected_cat = data.split("bcat_")[1]
        bf_gen = context.user_data["breakfast_generator"]

        items = bf_gen.get_items_by_category(selected_cat)
        if not items:
            await query.edit_message_text(
                text=f"В категории «{selected_cat}» нет блюд (завтрак).",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Назад", callback_data="breakfast")]
                ])
            )
            return RECIPES

        # Формируем кнопки для блюд
        keyboard_items = []
        for i, name in enumerate(items):
            callback_data = f"bitem_{i}"
            keyboard_items.append([InlineKeyboardButton(name, callback_data=callback_data)])

        context.user_data["bf_cat"] = selected_cat
        context.user_data["bf_map"] = {f"bitem_{i}": name for i, name in enumerate(items)}

        keyboard_items.append([InlineKeyboardButton("Назад", callback_data="breakfast")])
        await query.edit_message_text(
            text=f"Выберите блюдо из категории «{selected_cat}» (завтрак):",
            reply_markup=InlineKeyboardMarkup(keyboard_items)
        )
        return RECIPES

    elif data.startswith("bitem_"):
        # Детали блюда (завтрак)
        bf_gen = context.user_data.get("breakfast_generator")
        item_map = context.user_data.get("bf_map", {})
        item_key = data
        item_name = item_map.get(item_key)

        if not bf_gen or not item_name:
            # Handle error: generator or item not found
            await query.edit_message_text(
                text="Ошибка: Не удалось загрузить детали завтрака.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="breakfast")]])
            )
            return RECIPES

        details = bf_gen.get_item_details(item_name)
        selected_cat = context.user_data.get("bf_cat", "...") # Keep track of the category for back button

        # Store current recipe info for rating
        context.user_data['current_recipe_type'] = 'breakfast'
        context.user_data['current_recipe_name'] = item_name

        await query.edit_message_text(
            text=details,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ Оценить", callback_data="rate_recipe")], # Add Rate button
                [InlineKeyboardButton("Назад", callback_data=f"bcat_{selected_cat}")]
            ])
        )
        # Track RECIPE_VIEW action (assuming track_user decorator handles this based on state/handler)
        return RECIPES

    # ---------- Полдники ----------
    elif data == "poldnik":
        # При первом обращении - инициализируем PoldnikGenerator
        if "poldnik_generator" not in context.user_data:
            try:
                # Предположим, у вас CSV "Data/poldnik.csv"
                context.user_data["poldnik_generator"] = poldnik.PoldnikGenerator("Data/breakfast.csv")
                logger.info("PoldnikGenerator инициализирован.")
            except Exception as e:
                logger.error(f"Ошибка при загрузке полдников: {e}")
                await query.edit_message_text(
                    text=f"Ошибка при загрузке полдников: {e}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Назад", callback_data="start")]
                    ])
                )
                return RECIPES

        pd_gen = context.user_data["poldnik_generator"]
        categories = pd_gen.get_unique_categories()

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
            callback_data = f"pcat_{cat}"
            keyboard_cats.append([InlineKeyboardButton(cat, callback_data=callback_data)])

        keyboard_cats.append([InlineKeyboardButton("Назад", callback_data="start")])
        await query.edit_message_text(
            text="Выберите категорию (полдник):",
            reply_markup=InlineKeyboardMarkup(keyboard_cats)
        )
        return RECIPES

    elif data.startswith("pcat_"):
        selected_cat = data.split("pcat_")[1]
        pd_gen = context.user_data["poldnik_generator"]

        items = pd_gen.get_items_by_category(selected_cat)
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
            callback_data = f"pitem_{i}"
            keyboard_items.append([InlineKeyboardButton(name, callback_data=callback_data)])

        context.user_data["pd_cat"] = selected_cat
        context.user_data["pd_map"] = {f"pitem_{i}": name for i, name in enumerate(items)}

        keyboard_items.append([InlineKeyboardButton("Назад", callback_data="poldnik")])
        await query.edit_message_text(
            text=f"Выберите блюдо из категории «{selected_cat}» (полдник):",
            reply_markup=InlineKeyboardMarkup(keyboard_items)
        )
        return RECIPES

    elif data.startswith("pitem_"):
        # Детали блюда (полдник)
        pd_gen = context.user_data.get("poldnik_generator")
        item_map = context.user_data.get("pd_map", {})
        item_key = data
        item_name = item_map.get(item_key)

        if not pd_gen or not item_name:
             await query.edit_message_text(
                text="Ошибка: Не удалось загрузить детали полдника.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="poldnik")]])
            )
             return RECIPES

        details = pd_gen.get_item_details(item_name)
        selected_cat = context.user_data.get("pd_cat", "...")

        # Store current recipe info for rating
        context.user_data['current_recipe_type'] = 'poldnik'
        context.user_data['current_recipe_name'] = item_name

        await query.edit_message_text(
            text=details,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ Оценить", callback_data="rate_recipe")], # Add Rate button
                [InlineKeyboardButton("Назад", callback_data=f"pcat_{selected_cat}")]
            ])
        )
        return RECIPES

    # ---------- Обеды (lunch) ----------
    elif data == "lunch":
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

    elif data.startswith("category_"):
        category = data.split("_", 1)[1]
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
        context.user_data["current_category"] = category

        await query.edit_message_text(
            text=f"Выберите блюдо из категории '{category}':",
            reply_markup=InlineKeyboardMarkup(keyboard_dishes)
        )
        return RECIPES

    elif data.startswith("dish_"): # Lunch item details
        dish_key = data
        lunch_generator = context.user_data.get("lunch_generator")
        dish_mapping = context.user_data.get("dish_mapping", {})
        dish_name = dish_mapping.get(dish_key)
        current_category = context.user_data.get('current_category')

        if not lunch_generator or not dish_name or not current_category:
            await query.edit_message_text(
                text="Ошибка: Не удалось загрузить детали обеда.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="lunch")]])
            )
            return RECIPES

        details = lunch_generator.get_dish_details(dish_name)

        # Store current recipe info for rating
        context.user_data['current_recipe_type'] = 'lunch'
        context.user_data['current_recipe_name'] = dish_name

        await query.edit_message_text(
            text=details,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ Оценить", callback_data="rate_recipe")], # Add Rate button
                [InlineKeyboardButton("Назад", callback_data=f"category_{current_category}")]
            ])
        )
        return RECIPES

    # ---------- Напитки (drinks) ----------
    elif data == "drinks":
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
        drink_map = context.user_data.get("drinks_mapping", {})
        drink_key = data
        drink_name = drink_map.get(drink_key)
        current_cat = context.user_data.get('drinks_current_cat')

        if not drinks_generator or not drink_name or not current_cat:
            await query.edit_message_text(
                text="Ошибка: Не удалось загрузить детали напитка.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="drinks")]])
            )
            return RECIPES

        details = drinks_generator.get_drink_details(drink_name)

        # Store current recipe info for rating
        context.user_data['current_recipe_type'] = 'drink'
        context.user_data['current_recipe_name'] = drink_name

        await query.edit_message_text(
            text=details,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ Оценить", callback_data="rate_recipe")], # Add Rate button
                [InlineKeyboardButton("Назад", callback_data=f"drinks_cat_{current_cat}")]
            ])
        )
        return RECIPES

    # --- New handlers for rating ---

    elif data == "rate_recipe":
        # User clicked "Оценить"
        # Assuming track_user logs CLICK_RATE_BUTTON based on this data
        # or needs explicit logging here if track_user isn't sufficient.
        # Example explicit logging:
        # db = SessionLocal()
        # try:
        #     user_profile = get_or_create_user(db, user.id, ...) # Get user profile
        #     log_user_action(db, user_profile.id, ActionType.CLICK_RATE_BUTTON, details="Clicked rate button")
        # finally:
        #     db.close()

        # Show rating buttons
        rating_buttons = [
            InlineKeyboardButton(str(i), callback_data=f"rating_{i}") for i in range(1, 6)
        ]
        # Need recipe details again or just modify the keyboard? Modify keyboard is better.
        current_recipe_name = context.user_data.get('current_recipe_name', 'этот рецепт')

        await query.edit_message_text(
            text=f"👍 Отличный выбор! Оцените \"{current_recipe_name}\" от 1 до 5.\n"
                 f"Ваша оценка поможет нам улучшить рекомендации! 😉",
            reply_markup=InlineKeyboardMarkup([
                rating_buttons,
                # Option to go back without rating? Maybe add a Cancel or Back button here.
                # For now, only rating options.
            ])
        )
        return RECIPES # Stay in the recipes state

    elif data.startswith("rating_"):
        # User submitted a rating
        rating_value = int(data.split("_")[1])
        recipe_type = context.user_data.get('current_recipe_type')
        recipe_name = context.user_data.get('current_recipe_name')
        telegram_id = user.id

        if not recipe_type or not recipe_name:
            await query.edit_message_text(
                text="😕 Не удалось сохранить оценку. Попробуйте еще раз.",
                # Provide a way back, maybe to the recipe? Or menu?
                 reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("К рецептам", callback_data="healthy_recipes")]])
            )
            return RECIPES

        # --- Database Interaction ---
        db = SessionLocal()
        try:
            # We need the internal user ID, not just telegram_id.
            # Assuming a get_or_create_user function exists in crud.py
            from database.crud import get_or_create_user # Import here or at top
            user_profile = get_or_create_user(
                db=db,
                telegram_id=telegram_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )

            add_recipe_rating(
                db=db,
                user_id=user_profile.id,
                recipe_type=recipe_type,
                recipe_name=recipe_name,
                rating=rating_value
            )
            logger.info(f"User {telegram_id} rated '{recipe_name}' ({recipe_type}) as {rating_value}")

            # Assuming track_user logs SUBMIT_RATING based on this data
            # or needs explicit logging here:
            # log_user_action(db, user_profile.id, ActionType.SUBMIT_RATING, details=f"Rated {recipe_name} as {rating_value}")

            # Go back to the recipe view with a confirmation message?
            # Need the callback data for the previous step (e.g., "bcat_...", "category_...")
            # For simplicity, just show a thank you message and main recipe buttons
            await query.edit_message_text(
                text=f"⭐ Спасибо! Вы оценили \"{recipe_name}\" на {rating_value}."
                     f" Это очень поможет!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Назад", callback_data=context.user_data.get('last_recipe_callback', 'healthy_recipes'))],
                    [InlineKeyboardButton("Главное меню", callback_data="start")]
                ])
            )

        except Exception as e:
            logger.error(f"Failed to save rating for user {telegram_id}, recipe {recipe_name}: {e}")
            await query.answer("Не удалось сохранить оценку.", show_alert=True)
            # Maybe show the rating buttons again or go back?
            await query.edit_message_text(
                text="Произошла ошибка при сохранении оценки. Попробуйте позже.",
                 reply_markup=InlineKeyboardMarkup([
                     [InlineKeyboardButton("К рецептам", callback_data="healthy_recipes")],
                     [InlineKeyboardButton("Главное меню", callback_data="start")]
                 ])
            )
        finally:
            db.close()

        return RECIPES # Stay in recipe state or return to MENU? RECIPES seems okay.

    # Если никакая ветка не сработала
    logger.warning(f"Unhandled callback data in recipes_callback: {data}")
    # Fallback or error message
    await query.answer("Неизвестная команда.", show_alert=True)
    # Go back to menu?
    return await start_menu(update, context) # Safest fallback?

# Ensure the track_user decorator is applied if it handles action logging:
# recipes_callback = track_user(recipes_callback) # If not already done elsewhere

# Make sure add_recipe_rating is defined in crud.py and handles database session/commit/rollback.
# Make sure get_or_create_user is defined and works correctly.
# Consider database migrations if using Alembic or similar.
