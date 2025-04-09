from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
import subprocess
import logging
import os
import sqlite3
from datetime import datetime

# Определяем базовую директорию проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Настраиваем Flask с правильными путями для шаблонов и статических файлов
app = Flask(__name__, 
           template_folder=os.path.join(BASE_DIR),  # корневая директория для шаблонов
           static_folder=os.path.join(BASE_DIR, "static"))  # папка для статических файлов

# Настройка логирования
log_path = os.path.join(BASE_DIR, "flask_app.log")
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
)

# Инициализация базы данных для опросника
def init_survey_db():
    try:
        conn = sqlite3.connect('survey_responses.db')
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS survey_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT,
            gender TEXT,
            age INTEGER,
            diagnosis TEXT,
            family_history TEXT,
            bilirubin TEXT,
            childhood_jaundice TEXT,
            skin_yellowing TEXT,
            right_side_pain TEXT,
            other_liver_conditions TEXT,
            food_correlation TEXT,
            alcohol_correlation TEXT,
            fatigue_frequency TEXT,
            hunger_fatigue TEXT,
            exercise_feeling TEXT,
            overall_health TEXT,
            contact_info TEXT,
            submission_date TEXT
        )
        ''')
        conn.commit()
        conn.close()
        app.logger.info('Таблица survey_responses успешно инициализирована')
    except Exception as e:
        app.logger.error(f'Ошибка при инициализации базы данных опросника: {e}')

@app.route('/post-receive', methods=['POST'])
def post_receive():
    if request.method == 'POST':
        app.logger.info('Received webhook: %s', request.data)
        try:
            subprocess.check_call(['/root/project/Assistant/hooks/post-receive'])
        except subprocess.CalledProcessError as e:
            app.logger.error(f'Ошибка при вызове post-receive: {e}')
            return 'Internal Server Error', 500
        return '', 204
    else:
        return '', 400

# Простой маршрут для проверки работы сервера
@app.route('/')
def index():
    return "Сервер работает! Доступные маршруты: /survey, /test-text"

# Страница с опросником - приоритет на прямую отдачу файла
@app.route('/survey')
def survey():
    app.logger.info("Запрос к /survey получен")
    
    # Проверяем все возможные пути к файлу
    possible_paths = [
        os.path.join(BASE_DIR, 'mini_app', 'survey.html'),
        os.path.join(BASE_DIR, 'templates', 'mini_app', 'survey.html'),
        os.path.join(BASE_DIR, 'survey.html')
    ]
    
    # Логируем доступные пути для отладки
    for path in possible_paths:
        app.logger.info(f"Проверка пути: {path}, существует: {os.path.exists(path)}")
    
    # Перебираем все возможные пути и пытаемся отдать файл
    for path in possible_paths:
        if os.path.exists(path):
            app.logger.info(f"Найден файл по пути: {path}")
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return content
            except Exception as e:
                app.logger.error(f"Ошибка при чтении файла {path}: {e}")
    
    # Если файл не найден ни по одному пути, возвращаем ошибку
    app.logger.error("Файл анкеты не найден ни по одному из путей")
    return "Ошибка: файл анкеты не найден. Пожалуйста, сообщите администратору.", 500

# Тестовый маршрут с простым текстом - для проверки работы сервера
@app.route('/test-text')
def test_text():
    app.logger.info("Запрос к /test-text получен успешно")
    return "Тестовая страница работает! Это простой текст."

# Обработка отправки опросника
@app.route('/submit-survey', methods=['POST'])
def submit_survey():
    try:
        # Получаем данные формы
        telegram_id = request.form.get('telegram_id')
        gender = request.form.get('gender')
        age = request.form.get('age')
        diagnosis = request.form.get('diagnosis')
        family_history = request.form.get('family_history')
        bilirubin = request.form.get('bilirubin')
        childhood_jaundice = request.form.get('childhood_jaundice')
        skin_yellowing = request.form.get('skin_yellowing')
        right_side_pain = request.form.get('right_side_pain')
        other_liver_conditions = request.form.get('other_liver_conditions')
        food_correlation = request.form.get('food_correlation')
        alcohol_correlation = request.form.get('alcohol_correlation')
        fatigue_frequency = request.form.get('fatigue_frequency')
        hunger_fatigue = request.form.get('hunger_fatigue')
        exercise_feeling = request.form.get('exercise_feeling')
        overall_health = request.form.get('overall_health')
        contact_info = request.form.get('contact_info')
        
        # Текущая дата и время
        submission_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Логирование полученных данных
        app.logger.info(f'Получены данные опросника от пользователя {telegram_id}')
        
        # Сохраняем в базу данных
        conn = sqlite3.connect('survey_responses.db')
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO survey_responses (
            telegram_id, gender, age, diagnosis, family_history, 
            bilirubin, childhood_jaundice, skin_yellowing, right_side_pain, 
            other_liver_conditions, food_correlation, alcohol_correlation, 
            fatigue_frequency, hunger_fatigue, exercise_feeling, 
            overall_health, contact_info, submission_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            telegram_id, gender, age, diagnosis, family_history, 
            bilirubin, childhood_jaundice, skin_yellowing, right_side_pain, 
            other_liver_conditions, food_correlation, alcohol_correlation, 
            fatigue_frequency, hunger_fatigue, exercise_feeling, 
            overall_health, contact_info, submission_date
        ))
        conn.commit()
        conn.close()
        
        # Обновляем статус заполнения анкеты в основной базе данных бота
        if telegram_id:
            try:
                conn = sqlite3.connect('test.db')
                cursor = conn.cursor()
                
                # Проверяем, существует ли пользователь
                cursor.execute('SELECT id FROM client_profiles WHERE telegram_id = ?', (telegram_id,))
                user_row = cursor.fetchone()
                
                if user_row:
                    user_id = user_row[0]
                    
                    # Проверяем, есть ли запись о статусе анкеты
                    cursor.execute('SELECT id FROM user_survey_status WHERE user_id = ?', (user_id,))
                    survey_row = cursor.fetchone()
                    
                    if survey_row:
                        # Обновляем существующую запись
                        cursor.execute(
                            'UPDATE user_survey_status SET is_completed = ?, completed_at = ? WHERE user_id = ?',
                            (True, submission_date, user_id)
                        )
                    else:
                        # Создаем новую запись
                        cursor.execute(
                            'INSERT INTO user_survey_status (user_id, is_completed, completed_at, created_at) VALUES (?, ?, ?, ?)',
                            (user_id, True, submission_date, submission_date)
                        )
                    
                    conn.commit()
                    app.logger.info(f'Статус анкеты обновлен для пользователя {telegram_id}')
                else:
                    app.logger.warning(f'Пользователь с telegram_id {telegram_id} не найден в базе данных')
                
                conn.close()
            except Exception as e:
                app.logger.error(f'Ошибка при обновлении статуса анкеты: {e}')
        
        return jsonify({'success': True, 'message': 'Анкета успешно отправлена'})
    
    except Exception as e:
        app.logger.error(f'Ошибка при обработке отправки анкеты: {e}')
        return jsonify({'success': False, 'message': f'Ошибка при обработке анкеты: {str(e)}'}), 500

# Инициализируем базу данных при запуске сервера
init_survey_db()

if __name__ == '__main__':
    # Логируем базовую директорию и пути
    app.logger.info(f"Базовая директория проекта: {BASE_DIR}")
    app.logger.info(f"Папка шаблонов: {app.template_folder}")
    app.logger.info(f"Папка статики: {app.static_folder}")
    
    # Логируем доступность файла анкеты
    survey_file = os.path.join(BASE_DIR, 'mini_app', 'survey.html')
    app.logger.info(f"Файл анкеты: {survey_file}, существует: {os.path.exists(survey_file)}")
    
    # Запускаем сервер
    app.run(host='0.0.0.0', port=5000, debug=True)
