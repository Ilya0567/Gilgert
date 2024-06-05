import pandas as pd
from config import DATA_FILE
from random import randint

def save_user_data(timestamp, username, question, answer) -> str:
    """
    функция для сохранения вопросов от пользователей

    Args:
        timestamp (_type_): время в формате timestamp
        username (_type_): id пользователя
        question (_type_): вопрос от пользователя
        answer (_type_): ответ на вопрос
    """
    # генерируем уникальный номер сообщения
    id = "".join([str(randint(0, 9)) for i in range(7)])
    
    # открываем файл с данными
    user_data = pd.read_csv(DATA_FILE, index_col=False)
    
    # создаем новый датафрейм
    new_entry = pd.DataFrame([{
        "id": id,
        "timestamp": timestamp, 
        "username": username,
        "question": question,    
        "answer": answer
    }])
    
    # соединяем датасеты
    user_data = pd.concat([user_data, new_entry], ignore_index=True)
    # и сохраняем
    user_data.to_csv(DATA_FILE, index=False)
    
    return id