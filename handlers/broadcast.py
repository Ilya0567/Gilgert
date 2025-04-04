from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from datetime import datetime
import pytz
import logging
from sqlalchemy import and_

from database.database import SessionLocal
from database.crud import create_broadcast, get_or_create_user, get_all_active_users, mark_broadcast_sent
from utils.config import ADMIN_IDS
from database.models import BroadcastMessage, ClientProfile

logger = logging.getLogger(__name__)

# Состояния разговора для создания рассылки
ENTER_MESSAGE = 1
ENTER_TIME = 2

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

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает процесс создания рассылки"""
    if not await check_admin(update):
        return ConversationHandler.END
    
    await update.message.reply_text(
        "📝 Введите текст сообщения для рассылки:"
    )
    return ENTER_MESSAGE

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет текст сообщения и запрашивает время отправки"""
    if not await check_admin(update):
        return ConversationHandler.END
    
    # Сохраняем текст сообщения
    context.user_data['broadcast_message'] = update.message.text
    
    await update.message.reply_text(
        "🕒 Введите время отправки в формате 'ГГГГ-ММ-ДД ЧЧ:ММ'\n"
        "Например: 2024-04-05 15:30"
    )
    return ENTER_TIME

async def broadcast_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет время отправки и создает рассылку"""
    if not await check_admin(update):
        return ConversationHandler.END
    
    try:
        # Парсим время
        scheduled_time = datetime.strptime(update.message.text, "%Y-%m-%d %H:%M")
        scheduled_time = pytz.timezone('Europe/Moscow').localize(scheduled_time)
        
        # Проверяем, что время в будущем
        if scheduled_time <= datetime.now(pytz.timezone('Europe/Moscow')):
            await update.message.reply_text(
                "❌ Время должно быть в будущем.\n"
                "🕒 Введите время отправки в формате 'ГГГГ-ММ-ДД ЧЧ:ММ'\n"
                "Например: 2024-04-05 15:30"
            )
            return ENTER_TIME
        
        db = SessionLocal()
        try:
            # Получаем или создаем профиль админа
            admin_profile = get_or_create_user(
                db=db,
                telegram_id=str(update.effective_user.id),
                username=update.effective_user.username,
                first_name=update.effective_user.first_name,
                last_name=update.effective_user.last_name
            )
            
            # Создаем рассылку
            broadcast = create_broadcast(
                db=db,
                admin_id=admin_profile.id,
                message=context.user_data['broadcast_message'],
                scheduled_time=scheduled_time
            )
            
            await update.message.reply_text(
                f"✅ Рассылка создана!\n\n"
                f"📝 Текст: {context.user_data['broadcast_message']}\n"
                f"🕒 Время отправки: {scheduled_time.strftime('%Y-%m-%d %H:%M')}"
            )
            return ConversationHandler.END
            
        finally:
            db.close()
            
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат времени.\n"
            "🕒 Введите время отправки в формате 'ГГГГ-ММ-ДД ЧЧ:ММ'\n"
            "Например: 2024-04-05 15:30"
        )
        return ENTER_TIME

async def broadcast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет создание рассылки"""
    if not await check_admin(update):
        return ConversationHandler.END
    
    await update.message.reply_text("❌ Создание рассылки отменено.")
    return ConversationHandler.END

async def process_broadcasts(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Проверяет и отправляет запланированные рассылки"""
    db = SessionLocal()
    try:
        # Получаем все ожидающие рассылки
        broadcasts = get_pending_broadcasts(db)
        
        for broadcast in broadcasts:
            # Получаем всех активных пользователей
            users = get_active_users(db)
            
            # Отправляем сообщение каждому пользователю
            for user in users:
                try:
                    await context.bot.send_message(
                        chat_id=user.telegram_id,
                        text=broadcast.message
                    )
                except Exception as e:
                    logger.error(f"Failed to send broadcast to user {user.telegram_id}: {e}")
            
            # Помечаем рассылку как отправленную
            mark_broadcast_sent(db, broadcast.id)
            
    finally:
        db.close()

def get_pending_broadcasts(db):
    """Получает все рассылки, время отправки которых уже наступило"""
    now = datetime.now()
    return db.query(BroadcastMessage).filter(
        and_(
            BroadcastMessage.scheduled_time <= now,
            BroadcastMessage.is_sent == False
        )
    ).all()

def mark_broadcast_sent(db, broadcast_id):
    """Помечает рассылку как отправленную"""
    broadcast = db.query(BroadcastMessage).get(broadcast_id)
    if broadcast:
        broadcast.is_sent = True
        db.commit()

def get_active_users(db):
    """Получает список активных пользователей"""
    return db.query(ClientProfile).filter(ClientProfile.is_active == True).all()

def get_broadcast_handler() -> ConversationHandler:
    """Возвращает handler для создания рассылок"""
    return ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={
            ENTER_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message)
            ],
            ENTER_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_time)
            ],
        },
        fallbacks=[CommandHandler("cancel", broadcast_cancel)],
    ) 