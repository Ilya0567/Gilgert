from telegram import Update
from telegram.ext import ContextTypes
import logging

from utils.config import ADMIN_IDS

logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь админом"""
    return str(user_id) in ADMIN_IDS

async def check_admin(update: Update) -> bool:
    """Проверяет права админа и отправляет сообщение если нет доступа"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "⛔ У вас нет доступа к этой команде.\n"
            f"Ваш ID: {update.effective_user.id}"
        )
        return False
    return True

async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает список доступных команд для админа"""
    if not await check_admin(update):
        return

    commands_list = (
        "👑 *Команды администратора:*\n\n"
        "*Статистика:*\n"
        "📊 /stats\\_recipes \\- статистика по рецептам\n"
        "😊 /stats\\_health \\- статистика по настроению\n"
        "👥 /stats\\_users \\- статистика по пользователям\n"
        "❓ /stats\\_help \\- помощь по командам статистики\n\n"
        "*Рассылки:*\n"
        "📬 /broadcast \\- создать новую рассылку\n"
        "❌ /cancel \\- отменить создание рассылки\n\n"
        "*Таблицы базы данных:*\n"
        "👤 /table\\_users \\- таблица пользователей\n"
        "📝 /table\\_sessions \\- таблица сессий\n" 
        "🔄 /table\\_interactions \\- таблица взаимодействий\n"
        "⭐ /table\\_ratings \\- таблица оценок рецептов\n"
        "😊 /table\\_health \\- таблица проверок здоровья\n"
        "📢 /table\\_broadcasts \\- таблица рассылок"
    )

    await update.message.reply_text(
        commands_list,
        parse_mode='MarkdownV2'
    ) 