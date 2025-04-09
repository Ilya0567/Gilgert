from flask import Flask, request, jsonify, send_file
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Инициализация базы данных
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
    other_data TEXT,
    submission_date TEXT
)
''')
conn.commit()
conn.close()

# Маршрут для HTML файла анкеты
@app.route('/survey')
def survey():
    return send_file('mini_app/survey.html')

# Обработка отправки формы
@app.route('/submit-survey', methods=['POST'])
def submit_survey():
    try:
        # Получаем данные формы
        telegram_id = request.form.get('telegram_id')
        
        # Собираем все данные в JSON
        form_data = request.form.to_dict()
        
        # Сохраняем в базу данных
        conn = sqlite3.connect('survey_responses.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO survey_responses (telegram_id, gender, age, diagnosis, family_history, other_data, submission_date) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (
                telegram_id, 
                form_data.get('gender'),
                form_data.get('age'),
                form_data.get('diagnosis'),
                form_data.get('family_history'),
                str(form_data),  # сохраняем все данные как текст
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 