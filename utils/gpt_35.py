from openai import OpenAI
from utils.config import OPENAI_API_KEY
import openai
import json
import re
from typing import Optional, Dict, Any, List

client = OpenAI(api_key=OPENAI_API_KEY)

# Системное сообщение для задания контекста работы модели
SYSTEM_MESSAGE = """Ты дружелюбный и позитивный ассистент по здоровью и благополучию, который общается на русском языке. Твой стиль общения:
- Используй эмодзи, чтобы сделать общение более живым 😊
- Общайся на современном русском языке, можешь использовать разговорные выражения, когда это уместно
- Будь эмпатичным и показывай свою заинтересованность
- НИКОГДА не используй звездочки (*) в своих ответах для выделения текста
- Давай четкие и понятные ответы
- Можешь использовать молодежный сленг, если это уместно в контексте
- Всегда сохраняй позитивный и поддерживающий тон

Ты отвечаешь ТОЛЬКО на вопросы, связанные со следующими темами:
- Здоровье и медицина
- Правильное питание
- Фитнес и спорт
- Профилактика заболеваний
- Лекарства и их применение
- Психологическое благополучие
- Здоровый образ жизни

Когда пользователь спрашивает о рецептах, здоровом питании, диетах или просит предложить варианты блюд, используй функцию show_healthy_recipes для отображения меню с рецептами.

В зависимости от запроса пользователя, твой ответ должен быть адаптирован, но указывать на то, что будет показано общее меню категорий:

Примеры запросов и ответов:
- Запрос: "Какие есть рецепты для завтрака?"
  Ответ: "У меня есть отличные идеи здоровых завтраков! Сейчас покажу меню категорий, где ты сможешь выбрать интересующий тебя прием пищи 🍳"

- Запрос: "Посоветуй что приготовить на ужин"
  Ответ: "Конечно! У меня есть множество вариантов полезных ужинов. Сейчас покажу меню с разными категориями блюд на выбор 🍽️"

- Запрос: "Хочу рецепты правильного питания"
  Ответ: "Отлично! У меня есть подборка рецептов здорового питания для разных приемов пищи. Выбери категорию в меню ниже 🥗"

Если пользователь задает вопрос, не связанный с вышеперечисленными темами, вежливо объясни, что можешь консультировать только по вопросам здоровья и благополучия, и предложи задать вопрос из этой области."""

# Определение доступных функций
FUNCTIONS = [
    {
        "name": "show_healthy_recipes",
        "description": "Показать меню с подборкой здоровых рецептов пользователю. Пользователю будет показано меню с выбором категорий: завтраки, полдники, обеды, ужины. Вызывай эту функцию, когда пользователь интересуется рецептами, здоровым питанием, ищет блюда для конкретного приема пищи (завтрак, обед и т.д.), спрашивает о том, что можно приготовить, или просит предложить блюда.",
        "parameters": {
            "type": "object",
            "properties": {
                "context_response": {
                    "type": "string",
                    "description": "Краткий ответ пользователю в контексте его запроса перед показом меню. Ответ должен соответствовать запросу, но указывать, что пользователю будет показано общее меню категорий (завтрак, полдник, обед, ужин), где он сможет выбрать то, что его интересует. Например, если пользователь спросил о рецептах завтрака, то можно ответить 'Конечно, у меня есть отличные рецепты здоровых завтраков! Сейчас покажу меню, где ты сможешь выбрать категорию.'"
                }
            },
            "required": ["context_response"]
        }
    }
]

class ChatGPTClient:
    def __init__(self, api_key=None, model="gpt-3.5-turbo", temperature=0.9, max_tokens=2000):
        """
        Инициализация клиента ChatGPT.

        :param api_key: API-ключ для доступа к OpenAI (по умолчанию из конфига)
        :param model: Модель для использования (по умолчанию "gpt-3.5-turbo")
        :param temperature: Креативность модели (увеличена для более дружелюбных ответов)
        :param max_tokens: Максимальное количество токенов в ответе
        """
        self.api_key = api_key or OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key)
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
            # Отправляем запрос к API с функциями
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                functions=FUNCTIONS,
                function_call="auto"
            )
            
            response_message = response.choices[0].message
            
            # Проверяем, вызвал ли модель функцию
            if hasattr(response_message, 'function_call') and response_message.function_call:
                function_call = response_message.function_call
                
                # Если вызвана функция показа рецептов
                if function_call.name == "show_healthy_recipes":
                    try:
                        # Извлекаем контекстный ответ из аргументов функции
                        function_args = json.loads(function_call.arguments)
                        context_response = function_args.get("context_response", "Отлично! Сейчас покажу тебе наши здоровые рецепты 🥗")
                        
                        # Возвращаем специальный маркер с контекстным ответом
                        return f"FUNCTION_CALL:show_healthy_recipes:{context_response}"
                    except (json.JSONDecodeError, AttributeError, TypeError) as e:
                        print(f"Ошибка при парсинге аргументов функции: {e}")
                        # В случае ошибки, используем стандартный ответ
                        return "FUNCTION_CALL:show_healthy_recipes:Отлично! Сейчас покажу тебе наши здоровые рецепты 🥗"
            
            # Получаем текст ответа
            response_text = response_message.content.strip()
            
            # Удаляем звездочки из ответа
            response_text = re.sub(r'\*', '', response_text)
            
            # Возвращаем текст ответа
            return response_text
            
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
    


