#!/bin/bash

# Скрипт для перезапуска бота и обеспечения его постоянной работы
# Сохраните этот файл как restart_bot.sh и сделайте его исполняемым:
# chmod +x restart_bot.sh

# Настройка переменных
BOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_FILE="$BOT_DIR/restart_logs.log"
WEBHOOK_MODE=true  # Установите false для запуска в режиме polling

echo "$(date): Перезапуск бота" >> "$LOG_FILE"

# Убить существующие процессы бота, если они есть
pkill -f "python3 $BOT_DIR/assistant.py"
sleep 2

# Проверка наличия файла .pid и его удаление
PID_FILE="$BOT_DIR/bot.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null; then
        echo "$(date): Завершение процесса бота с PID $OLD_PID" >> "$LOG_FILE"
        kill -9 "$OLD_PID" 2>/dev/null
    fi
    rm "$PID_FILE"
fi

# Переход в директорию бота
cd "$BOT_DIR" || exit 1

# Запуск бота в режиме webhook или polling
if [ "$WEBHOOK_MODE" = true ]; then
    echo "$(date): Запуск бота в режиме webhook" >> "$LOG_FILE"
    nohup python3 assistant.py --webhook > bot_output.log 2>&1 &
else
    echo "$(date): Запуск бота в режиме polling" >> "$LOG_FILE"
    nohup python3 assistant.py > bot_output.log 2>&1 &
fi

# Сохранение PID нового процесса
echo $! > "$PID_FILE"
echo "$(date): Бот запущен с PID $(cat $PID_FILE)" >> "$LOG_FILE"

# Проверка успешности запуска через 5 секунд
sleep 5
if ps -p "$(cat $PID_FILE)" > /dev/null; then
    echo "$(date): Бот успешно запущен и работает" >> "$LOG_FILE"
else
    echo "$(date): ОШИБКА: Бот не запустился" >> "$LOG_FILE"
fi 