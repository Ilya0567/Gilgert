from flask import Flask, request, jsonify, render_template, send_from_directory
import subprocess
import logging
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(BASE_DIR, "flask_app.log")  # корректный путь

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path),  # Логи в файл
        logging.StreamHandler()         # Логи в консоль (по желанию)
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
        # Логируем входящий запрос
        app.logger.info('Received webhook: %s', request.data)
        # Выполнить ваш скрипт post-receive
        try:
            subprocess.check_call(['/root/project/Assistant/hooks/post-receive'])
        except subprocess.CalledProcessError as e:
            app.logger.error(f'Ошибка при вызове post-receive: {e}')
            return 'Internal Server Error', 500
        return '', 204
    else:
        return '', 400

# Страница с опросником
@app.route('/survey')
def survey():
    return render_template('mini_app/survey.html')

# Статические файлы из mini_app
@app.route('/mini_app/<path:path>')
def send_mini_app(path):
    return send_from_directory('mini_app', path)

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
    app.run(host='0.0.0.0', port=5000)
