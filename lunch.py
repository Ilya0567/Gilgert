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

    def get_lunch_names(self):
        """Возвращает строку с названиями блюд для текущего обеда"""
        lunch_names = []
        for category, dish in self.lunch.items():
            if dish:
                lunch_names.append(f"{dish}")
            else:
                lunch_names.append(f"{category}: Нет доступного блюда")
        return "\n".join(lunch_names)  # Строка с названием блюд

    def get_ingredients(self):
        """Возвращает строку с составами для всех выбранных блюд"""
        ingredients = []
        for category, dish in self.lunch.items():
            if dish and dish != "Нет доступного блюда":
                ingredient = self.df[self.df["Название завтрака:"] == dish]["Ингредиенты на 1 порцию:"]
                if not ingredient.empty:
                    ingredients.append(f"{dish}:\nИнгредиенты: {ingredient.iloc[0]}")
                else:
                    ingredients.append(f"{dish}:\nИнгредиенты не найдены")
            else:
                ingredients.append(f"Нет доступного блюда")
        return "\n\n".join(ingredients)  # Строка с составами блюд

    def get_cooking_instructions(self):
        """Возвращает строку с рецептами для всех выбранных блюд"""
        instructions = []
        for category, dish in self.lunch.items():
            if dish and dish != "Нет доступного блюда":
                instruction = self.df[self.df["Название завтрака:"] == dish]["Приготовление:"]
                if not instruction.empty:
                    instructions.append(f"{dish}:\nПриготовление: {instruction.iloc[0]}")
                else:
                    instructions.append(f"{dish}:\nСпособ приготовления не найден")
            else:
                instructions.append(f"Нет доступного блюда")
        return "\n\n".join(instructions)  # Строка с рецептами блюд
