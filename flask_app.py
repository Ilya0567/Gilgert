from flask import Flask, request, jsonify, send_file
import logging
import os
import sqlite3
import subprocess
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
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Сервер анкет Жильбера</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            h1 { color: #2c3e50; }
            .card { 
                background-color: #f8f9fa; 
                border-radius: 5px; 
                padding: 20px; 
                margin-bottom: 20px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            a.btn {
                display: inline-block;
                background-color: #3498db;
                color: white;
                text-decoration: none;
                padding: 10px 20px;
                border-radius: 5px;
                margin-right: 10px;
            }
            a.btn:hover {
                background-color: #2980b9;
            }
        </style>
    </head>
    <body>
        <h1>Сервер анкет для людей с синдромом Жильбера</h1>
        
        <div class="card">
            <h2>Системный статус</h2>
            <p>✅ Сервер работает нормально</p>
            <p>✅ Доступны все функции</p>
        </div>
        
        <div class="card">
            <h2>Доступные страницы</h2>
            <p>
                <a href="/survey" class="btn">Заполнить анкету</a>
                <a href="/stats" class="btn">Просмотреть статистику</a>
            </p>
        </div>
    </body>
    </html>
    """

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

# Маршрут для просмотра статистики заполнения анкет (для админов)
@app.route('/stats', methods=['GET', 'POST'])
def stats():
    try:
        # Проверка авторизации через параметр password
        password = request.args.get('password')
        admin_password = "gilbert_stats_2023"  # Простой пароль для доступа
        
        # Если пароль не предоставлен или неверный, показываем форму авторизации
        if password != admin_password:
            app.logger.info("Попытка доступа к статистике без пароля или с неверным паролем")
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Доступ к статистике</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                    h1 { color: #2c3e50; }
                    .card { 
                        background-color: #f8f9fa; 
                        border-radius: 5px; 
                        padding: 20px; 
                        margin-bottom: 20px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    }
                    input[type="password"] {
                        padding: 8px;
                        width: 100%;
                        max-width: 300px;
                        margin-bottom: 15px;
                    }
                    button {
                        background-color: #3498db;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        cursor: pointer;
                    }
                    button:hover {
                        background-color: #2980b9;
                    }
                </style>
            </head>
            <body>
                <h1>Доступ к статистике</h1>
                
                <div class="card">
                    <h2>Требуется авторизация</h2>
                    <p>Для просмотра статистики введите пароль администратора:</p>
                    <form action="/stats" method="get">
                        <input type="password" name="password" placeholder="Введите пароль">
                        <button type="submit">Войти</button>
                    </form>
                </div>
            </body>
            </html>
            """
        
        app.logger.info("Успешный запрос статистики анкет")
        
        # Подключаемся к БД с анкетами
        conn = sqlite3.connect('survey_responses.db')
        cursor = conn.cursor()
        
        # Общее количество заполненных анкет
        cursor.execute('SELECT COUNT(*) FROM survey_responses')
        total_surveys = cursor.fetchone()[0]
        
        # Статистика по полу
        cursor.execute('SELECT gender, COUNT(*) FROM survey_responses GROUP BY gender')
        gender_stats = cursor.fetchall()
        
        # Средний возраст
        cursor.execute('SELECT AVG(age) FROM survey_responses WHERE age IS NOT NULL')
        avg_age = cursor.fetchone()[0]
        
        # Статистика по диагнозу
        cursor.execute('SELECT diagnosis, COUNT(*) FROM survey_responses GROUP BY diagnosis')
        diagnosis_stats = cursor.fetchall()
        
        # Последние 10 заполнивших
        cursor.execute('SELECT telegram_id, submission_date FROM survey_responses ORDER BY submission_date DESC LIMIT 10')
        recent_submissions = cursor.fetchall()
        
        conn.close()
        
        # Формируем HTML с статистикой
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Статистика заполнения анкет</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; }}
                .stat-card {{ 
                    background-color: #f8f9fa; 
                    border-radius: 5px; 
                    padding: 15px; 
                    margin-bottom: 20px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                tr:hover {{ background-color: #f5f5f5; }}
                .back-link {{
                    display: inline-block;
                    margin-top: 20px;
                    color: #3498db;
                    text-decoration: none;
                }}
                .back-link:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <h1>Статистика заполнения анкет</h1>
            
            <div class="stat-card">
                <h2>Общие данные</h2>
                <p>Всего заполнено анкет: <strong>{total_surveys}</strong></p>
                <p>Средний возраст: <strong>{avg_age:.1f if avg_age else 'Нет данных'}</strong></p>
            </div>
            
            <div class="stat-card">
                <h2>Распределение по полу</h2>
                <table>
                    <tr>
                        <th>Пол</th>
                        <th>Количество</th>
                    </tr>
                    {''.join(f'<tr><td>{"Мужской" if g[0] == "male" else "Женский" if g[0] == "female" else g[0]}</td><td>{g[1]}</td></tr>' for g in gender_stats)}
                </table>
            </div>
            
            <div class="stat-card">
                <h2>Распределение по диагнозу</h2>
                <table>
                    <tr>
                        <th>Диагноз</th>
                        <th>Количество</th>
                    </tr>
                    {''.join(f'<tr><td>{get_diagnosis_name(d[0])}</td><td>{d[1]}</td></tr>' for d in diagnosis_stats)}
                </table>
            </div>
            
            <div class="stat-card">
                <h2>Последние заполненные анкеты</h2>
                <table>
                    <tr>
                        <th>Telegram ID</th>
                        <th>Дата заполнения</th>
                    </tr>
                    {''.join(f'<tr><td>{r[0]}</td><td>{r[1]}</td></tr>' for r in recent_submissions)}
                </table>
            </div>
            
            <a href="/" class="back-link">← Вернуться на главную</a>
        </body>
        </html>
        """
        return html
    except Exception as e:
        app.logger.error(f"Ошибка при формировании статистики: {e}")
        return f"Ошибка при получении статистики: {e}", 500

# Вспомогательная функция для отображения диагнозов в читаемом виде
def get_diagnosis_name(code):
    diagnoses = {
        'yes_doctor': 'Диагностирован врачом',
        'yes_genetic': 'Подтвержден генетическим тестом',
        'no': 'Не диагностирован',
        'not_sure': 'Не уверен'
    }
    return diagnoses.get(code, code)


# Обработчик вебхуков от GitHub/GitLab для обновления кода
@app.route('/post-receive', methods=['POST'])
def post_receive():
    if request.method == 'POST':
        # Логируем входящий запрос
        app.logger.info('Received webhook: %s', request.data)
        # Выполнить ваш скрипт post-receive
        subprocess.call(['/root/project/Assistant/hooks/post-receive'])
        return '', 204
    else:
        return '', 400

# Вебхук для телеграм-бота (если требуется)
@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    app.logger.info("Получен вебхук от Telegram")
    try:
        # Перенаправление данных боту (в случае совместного размещения бота и веб-сервера)
        # Фактическая реализация зависит от структуры вашего проекта
        return jsonify({"success": True}), 200
    except Exception as e:
        app.logger.error(f"Ошибка при обработке Telegram вебхука: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.logger.info("Запуск Flask-приложения")
    app.logger.info(f"Рабочая директория: {os.getcwd()}")
    app.logger.info(f"Содержимое папки: {os.listdir('.')}")
    app.logger.info(f"Файл survey.html существует: {os.path.exists('survey.html')}")
    app.run(host='0.0.0.0', port=5000, debug=True)
