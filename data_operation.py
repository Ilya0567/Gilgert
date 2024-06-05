import pandas as pd
from config import DATA_FILE

def save_user_data(timestamp, username, question, answer):
    """
    функция для сохранения вопросов от пользователей

    Args:
        timestamp (_type_): время в формате timestamp
        username (_type_): id пользователя
        question (_type_): вопрос от пользователя
        answer (_type_): ответ на вопрос
    """
    # открываем файл с данными
    user_data = pd.read_csv(DATA_FILE, index_col=False)
    # создаем новый датафрейм
    new_entry = pd.DataFrame([{
        "timestamp": timestamp, 
        "username": username,
        "question": question,    
        "answer": answer
    }])
    
    # соединяем датасеты
    user_data = pd.concat([user_data, new_entry], ignore_index=True)
    # и сохраняем
    user_data.to_csv(DATA_FILE, index=False)