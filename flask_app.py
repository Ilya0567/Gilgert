from flask import Flask, request, jsonify, send_file
import logging
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("flask_app.log"),
        logging.StreamHandler()
    ]
)

# Маршрут для проверки работы сервера
@app.route('/')
def index():
    return "Сервер работает"

# Простой маршрут с текстом для тестирования
@app.route('/test-text')
def test_text():
    app.logger.info("Запрос к /test-text получен")
    return "Это тестовая страница"

# Вот отсюда важно - очень простая отдача HTML-файла
@app.route('/survey')
def survey():
    app.logger.info("Запрос к /survey получен")
    # Прямой путь к файлу
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'survey.html')
    
    try:
        app.logger.info(f"Открываю файл: {html_path}")
        app.logger.info(f"Файл существует: {os.path.exists(html_path)}")
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return html_content
    except Exception as e:
        app.logger.error(f"Ошибка при чтении файла: {e}")
        return f"Ошибка при загрузке анкеты: {e}", 500

# Обработка отправки опросника
@app.route('/submit-survey', methods=['POST'])
def submit_survey():
    try:
        # Получаем данные формы
        telegram_id = request.form.get('telegram_id')
        app.logger.info(f"Получены данные формы, telegram_id: {telegram_id}")
        
        # Собираем все данные в словарь
        form_data = {
            'telegram_id': telegram_id,
            'gender': request.form.get('gender'),
            'age': request.form.get('age'),
            'diagnosis': request.form.get('diagnosis'),
            'family_history': request.form.get('family_history'),
            'bilirubin': request.form.get('bilirubin'),
            'childhood_jaundice': request.form.get('childhood_jaundice'),
            'skin_yellowing': request.form.get('skin_yellowing'),
            'right_side_pain': request.form.get('right_side_pain'),
            'other_liver_conditions': request.form.get('other_liver_conditions'),
            'food_correlation': request.form.get('food_correlation'),
            'alcohol_correlation': request.form.get('alcohol_correlation'),
            'fatigue_frequency': request.form.get('fatigue_frequency'),
            'hunger_fatigue': request.form.get('hunger_fatigue'),
            'exercise_feeling': request.form.get('exercise_feeling'),
            'overall_health': request.form.get('overall_health'),
            'contact_info': request.form.get('contact_info')
        }
        
        # Сохраняем в БД
        conn = sqlite3.connect('survey_responses.db')
        cursor = conn.cursor()
        
        # Создаем таблицу, если ее нет
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
        
        # Текущая дата и время
        submission_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Вставляем данные
        cursor.execute('''
        INSERT INTO survey_responses (
            telegram_id, gender, age, diagnosis, family_history, 
            bilirubin, childhood_jaundice, skin_yellowing, right_side_pain, 
            other_liver_conditions, food_correlation, alcohol_correlation, 
            fatigue_frequency, hunger_fatigue, exercise_feeling, 
            overall_health, contact_info, submission_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            form_data['telegram_id'], form_data['gender'], form_data['age'], 
            form_data['diagnosis'], form_data['family_history'],
            form_data['bilirubin'], form_data['childhood_jaundice'], 
            form_data['skin_yellowing'], form_data['right_side_pain'],
            form_data['other_liver_conditions'], form_data['food_correlation'], 
            form_data['alcohol_correlation'], form_data['fatigue_frequency'],
            form_data['hunger_fatigue'], form_data['exercise_feeling'],
            form_data['overall_health'], form_data['contact_info'], submission_date
        ))
        
        conn.commit()
        conn.close()
        app.logger.info("Анкета успешно сохранена")
        
        return jsonify({'success': True, 'message': 'Анкета отправлена успешно'})
    
    except Exception as e:
        app.logger.error(f"Ошибка при обработке анкеты: {e}")
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'}), 500

if __name__ == '__main__':
    app.logger.info("Запуск Flask-приложения")
    app.logger.info(f"Рабочая директория: {os.getcwd()}")
    app.logger.info(f"Содержимое папки: {os.listdir('.')}")
    app.logger.info(f"Файл survey.html существует: {os.path.exists('survey.html')}")
    app.run(host='0.0.0.0', port=5000, debug=True)
