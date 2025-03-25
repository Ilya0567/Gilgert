from flask import Flask, request
import subprocess
import logging

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('root/project/Assistant/flask_app.log'),  # Логи в файл
        logging.StreamHandler()  # Логи в консоль (по желанию)
    ]
)


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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)