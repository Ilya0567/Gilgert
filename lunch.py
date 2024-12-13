import pandas as pd

class LunchGenerator:
    def __init__(self, data_source):
        try:
            self.df = pd.read_csv(data_source)
            print("DataFrame загружен успешно!")
        except Exception as e:
            print(f"Ошибка при загрузке DataFrame: {e}")
            self.df = None

        if self.df is None or self.df.empty:
            raise ValueError("Не удалось загрузить данные. Проверьте файл.")
        
        self.df.columns = self.df.columns.str.strip()
        self.df["Тип блюда"] = self.df["Тип блюда"].str.strip()

        self.lunch = {
            "Первое блюдо": None,
            "салат": None,
            "гарниры": None,
            "второе блюдо": None
        }
        self.create_lunch()

    def create_lunch(self):
        """Создаёт обед, выбирая случайное блюдо для каждой категории"""
        categories = list(self.lunch.keys())
        for category in categories:
            available_dishes = self.df[self.df["Тип блюда"] == category]
            if not available_dishes.empty:
                selected_dish = available_dishes.sample(1).iloc[0]
                self.lunch[category] = selected_dish["Название завтрака:"]
            else:
                self.lunch[category] = None

    def change_dish(self, category):
        """
        Меняет текущее блюдо в указанной категории на случайное блюдо того же типа.
        """
        if category not in self.lunch:
            raise ValueError(f"Категория '{category}' не найдена в текущем обеде.")

        current_dish = self.lunch[category]
        available_dishes = self.df[self.df["Тип блюда"] == category]
        
        if not available_dishes.empty:
            available_dishes = available_dishes[available_dishes["Название завтрака:"] != current_dish]
            if not available_dishes.empty:
                selected_dish = available_dishes.sample(1).iloc[0]
                self.lunch[category] = selected_dish["Название завтрака:"]
                return self.lunch[category]
            else:
                return f"Все доступные блюда категории '{category}' уже выбраны."
        else:
            return f"Нет доступных блюд для категории '{category}'."

    def add_emoji_to_dish(self, category, dish):
        """Добавляет эмодзи к категории блюда"""
        emojis = {
            "Первое блюдо": "🍲",    # Суп
            "второе блюдо": "🍖",   # Основное блюдо
            "гарниры": "🍚",        # Гарнир
            "салат": "🥗"           # Салат
        }
        emoji = emojis.get(category, "🍽")
        if dish:
            return f"                    {emoji} {dish}"
        else:
            return f"                    {category}: Нет доступного блюда"

    def get_lunch_names(self):
        """Возвращает строку с названиями блюд для текущего обеда, с эмодзи"""
        lunch_names = []
        for category, dish in self.lunch.items():
            lunch_names.append(self.add_emoji_to_dish(category, dish))
        return "\n".join(lunch_names)

    def get_dish_details(self, dish_name):
        """
        Возвращает ингредиенты и способ приготовления для конкретного блюда.
        """
        if dish_name not in self.df["Название завтрака:"].values:
            return f"Блюдо '{dish_name}' не найдено в базе данных."

        dish_data = self.df[self.df["Название завтрака:"] == dish_name].iloc[0]
        ingredients = dish_data["Ингредиенты на 1 порцию:"] if not pd.isna(dish_data["Ингредиенты на 1 порцию:"]) else "Ингредиенты не найдены."
        preparation = dish_data["Приготовление:"] if not pd.isna(dish_data["Приготовление:"]) else "Способ приготовления не найден."

        return (
            f"🍴 {dish_name}\n\n"
            f"Ингредиенты:\n{ingredients}\n\n"
            f"Приготовление:\n{preparation}"
        )
