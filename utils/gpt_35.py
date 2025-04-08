from openai import OpenAI
from utils.config import OPENAI_API_KEY
import openai
import json
from typing import Optional, Dict, Any, List

client = OpenAI(api_key=OPENAI_API_KEY)

# Системное сообщение для задания контекста работы модели
SYSTEM_MESSAGE = """You are a helpful AI assistant that provides clear and accurate responses."""

class ChatGPTClient:
    def __init__(self, api_key=OPENAI_API_KEY, model="gpt-4-0125-preview", temperature=0.9, max_tokens=100):
        """
        Инициализация клиента ChatGPT.

        :param api_key: API-ключ для доступа к OpenAI (по умолчанию из конфига)
        :param model: Модель для использования (по умолчанию "gpt-4-0125-preview")
        :param temperature: Креативность модели (увеличена для более дружелюбных ответов)
        :param max_tokens: Максимальное количество токенов в ответе
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate_response(self, user_message: str, system_message: dict = None, message_history: list = None) -> str:
        """
        Генерирует ответ на сообщение пользователя
        
        Args:
            user_message (str): Сообщение пользователя
            system_message (dict, optional): Системное сообщение. По умолчанию используется SYSTEM_MESSAGE.
            message_history (list, optional): История сообщений для контекста. По умолчанию None.
            
        Returns:
            str: Ответ модели
        """
        # Формируем сообщения для отправки
        messages = []
        
        # Добавляем системное сообщение
        if system_message is None:
            messages.append({"role": "system", "content": SYSTEM_MESSAGE})
        else:
            if isinstance(system_message, str):
                messages.append({"role": "system", "content": system_message})
            else:
                messages.append(system_message)
                
        # Добавляем историю сообщений если она есть
        if message_history:
            messages.extend(message_history)
                
        # Добавляем сообщение пользователя
        messages.append({"role": "user", "content": user_message})
        
        try:
            # Отправляем запрос к API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Возвращаем текст ответа
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Ошибка при генерации ответа: {e}")
            return "Извини, произошла ошибка при генерации ответа 😔 Попробуй еще раз!"

# Пример использования
if __name__ == "__main__":
    
    KEY = "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"

    client = ChatGPTClient(api_key=KEY)

    user_input = "Что такое синдром собака?"
    response = client.generate_response(system_message=SYSTEM_MESSAGE, user_message=user_input)
    print(response)
    


