import pandas as pd


class BreakfastGenerator:
    """
    Класс для работы с таблицей завтраков/полдников (один файл breakfast.csv).
    Структура колонок:
      - Название
      - Ингредиенты на 1 порцию:
      - Приготовление:
      - Какое блюдо   (например, 'завтрак' или 'полдник')
      - Блюдо из      (подкатегория, например 'каша', 'омлет', 'бутерброды' и т.д.)
    """

    def __init__(self, data_source):
        """
        data_source: путь к файлу (CSV или Excel) с завтраками/полдниками.
        Например: 'Data/breakfast.csv'
        """
        try:
            self.df = pd.read_csv(data_source)
            print("Breakfast DataFrame загружен успешно!")
        except Exception as e:
            print(f"Ошибка при загрузке Breakfast DataFrame: {e}")
            self.df = None

        if self.df is None or self.df.empty:
            raise ValueError("Не удалось загрузить данные о завтраках/полдниках.")

        # Проверяем наличие нужных колонок
        needed_cols = ["Название завтрака:", "Ингредиенты на 1 порцию:", "Приготовление:", "Какое блюдо", "Блюдо из"]
        for col in needed_cols:
            if col not in self.df.columns:
                raise ValueError(f"В файле с завтраками/полдниками не найдена колонка '{col}'")

        self.df.columns = self.df.columns.str.strip()

    def filter_by_meal_type(self, meal_type: str):
        """
        Фильтруем датафрейм по колонке 'Какое блюдо' (например, 'завтрак' или 'полдник').
        Возвращаем подтаблицу.
        """
        # Предполагается, что в 'Какое блюдо' лежат значения 'завтрак' или 'полдник'.
        return self.df

    def get_unique_categories(self, meal_type: str):
        """
        Возвращает список уникальных значений из 'Блюдо из' для указанного типа (завтрак/полдник).
        """
        sub_df = self.filter_by_meal_type(meal_type)
        return sorted(sub_df["Блюдо из"].dropna().unique().tolist())

    def get_items_by_category(self, meal_type: str, category: str):
        """
        Возвращает список Названий для указанного meal_type (завтрак/полдник) и категории (колонка 'Блюдо из').
        """
        sub_df = self.filter_by_meal_type(meal_type)
        sub_df = sub_df[sub_df["Блюдо из"] == category]
        return sub_df["Название завтрака:"].tolist()

    def get_item_details(self, item_name: str):
        """
        Возвращает строку с названием, ингредиентами и приготовлением для выбранного блюда.
        """
        row = self.df[self.df["Название завтрака:"] == item_name]
        if row.empty:
            return f"Блюдо «{item_name}» не найдено."

        ingredients = row.iloc[0]["Ингредиенты на 1 порцию:"]
        preparation = row.iloc[0]["Приготовление:"]
        return (
            f"🍳 {item_name}\n\n"
            f"Ингредиенты:\n{ingredients}\n\n"
            f"Приготовление:\n{preparation}"
        )
