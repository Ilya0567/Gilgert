from utils.gpt_35 import ChatGPTClient, SYSTEM_MESSAGE

def main():
    # Инициализируем клиент
    client = ChatGPTClient()
    
    print("Привет! Я твой дружелюбный ассистент 👋")
    print("Напиши 'выход' для завершения")
    
    while True:
        # Получаем сообщение от пользователя
        user_input = input("\nТы: ")
        
        if user_input.lower() == 'выход':
            print("\nПока! Было приятно пообщаться 👋")
            break
            
        # Генерируем ответ
        response = client.generate_response(user_input, SYSTEM_MESSAGE)
        
        # Выводим ответ
        print(f"\nАссистент: {response}")

if __name__ == "__main__":
    main() 