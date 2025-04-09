import os
import shutil

# Копируем файл из templates/mini_app в mini_app
os.makedirs('mini_app', exist_ok=True)
shutil.copy2('templates/mini_app/survey.html', 'mini_app/survey.html')
print("Файл survey.html скопирован в папку mini_app") 