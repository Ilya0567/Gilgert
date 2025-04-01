from flask import Flask, request
import subprocess
import logging
import os
app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(BASE_DIR, "flask_app.log")  # ✅ корректный путь
# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path),  # Логи в файл
        logging.StreamHandler()  # Логи в консоль (по желанию)
    ]
)


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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
