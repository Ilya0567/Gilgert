import pandas as pd

class PoldnikGenerator:
    """
    Класс для работы с таблицей 'полдники' (poldnik.csv).
    Предполагаем, что столбцы:
      - Название
      - Ингредиенты на 1 порцию:
      - Приготовление:
      - Блюдо из (подкатегория)
      - Какое блюдо (можно не использовать, если весь файл — только про полдники)
    """

    def __init__(self, data_source):
        try:
            self.df = pd.read_csv(data_source)
            print("Poldnik DataFrame загружен успешно!")
        except Exception as e:
            print(f"Ошибка при загрузке Poldnik DataFrame: {e}")
            self.df = None

        if self.df is None or self.df.empty:
            raise ValueError("Не удалось загрузить данные о полдниках.")

        # Проверяем наличие нужных колонок
        needed_cols = ["Название завтрака:", "Ингредиенты на 1 порцию:", "Приготовление:", "Блюдо из"]
        for col in needed_cols:
            if col not in self.df.columns:
                raise ValueError(f"В poldnik.csv не найдена колонка '{col}'")

        self.df.columns = self.df.columns.str.strip()

    def get_unique_categories(self):
        """Возвращает список уникальных значений из 'Блюдо из'."""
        return sorted(self.df["Блюдо из"].dropna().unique().tolist())

    def get_items_by_category(self, category: str):
        """Возвращает список 'Название' блюд, у которых 'Блюдо из' == category."""
        sub_df = self.df[self.df["Блюдо из"] == category]
        return sub_df["Название завтрака:"].tolist()

    def get_item_details(self, item_name: str):
        """Возвращает строку с названием, ингредиентами и приготовлением."""
        row = self.df[self.df["Название завтрака:"] == item_name]
        if row.empty:
            return f"Блюдо «{item_name}» не найдено (полдник)."

        ingredients = row.iloc[0]["Ингредиенты на 1 порцию:"]
        preparation = row.iloc[0]["Приготовление:"]
        return (
            f"🍪 {item_name}\n\n"
            f"Ингредиенты:\n{ingredients}\n\n"
            f"Приготовление:\n{preparation}"
        )
