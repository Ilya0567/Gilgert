import pandas as pd

class DrinksGenerator:
    """
    Класс для работы с таблицей напитков.
    Предполагается, что у вас есть Excel/CSV-файл с колонками:
      - №
      - Название
      - Ингредиенты на 1 порцию:
      - Приготовление:
      - Какое блюдо (должно быть "напитки")
      - Блюдо из (категория, например "чай" / "кофе" / ...)
    """

    def __init__(self, data_source):
        """
        data_source: путь к файлу (например, "Data/Напитки.csv" или Excel).
        Если Excel, используйте pd.read_excel(...).
        Если CSV, используйте pd.read_csv(...).
        Тут для примера CSV.
        """
        try:
            # Если у вас Excel, сделайте:
            # self.df = pd.read_excel(data_source, header=1)
            self.df = pd.read_csv(data_source)
            print("Drinks DataFrame загружен успешно!")
        except Exception as e:
            print(f"Ошибка при загрузке Drinks DataFrame: {e}")
            self.df = None

        if self.df is None or self.df.empty:
            raise ValueError("Не удалось загрузить данные о напитках. Проверьте файл.")

        # Убедимся, что нужные колонки есть
        # (подставьте реальные названия колонок, если отличаются)
        needed_cols = ["Название:", "Ингредиенты на 1 порцию:", "Приготовление:", "Какое блюдо", "Блюдо из"]
        for col in needed_cols:
            if col not in self.df.columns:
                raise ValueError(f"В файле с напитками не найдена колонка '{col}'")

        # Очистка пробелов и т.п.
        self.df.columns = self.df.columns.str.strip()

    def get_unique_categories(self):
        """
        Возвращает список уникальных значений из столбца 'Блюдо из'.
        Это и будут подкатегории напитков (например, 'чай', 'кофе' и т.д.).
        """
        return sorted(self.df["Блюдо из"].dropna().unique().tolist())

    def get_drinks_by_category(self, cat: str):
        """
        Возвращает список (строк) названий напитков, у которых 'Блюдо из' == cat.
        """
        subset = self.df[self.df["Блюдо из"] == cat]
        return subset["Название"].tolist()

    def get_drink_details(self, drink_name: str):
        """
        Возвращает строку с названием, ингредиентами и приготовлением.
        """
        row = self.df[self.df["Название:"] == drink_name]
        if row.empty:
            return f"Напиток «{drink_name}» не найден."

        ingredients = row.iloc[0]["Ингредиенты на 1 порцию:"]
        preparation = row.iloc[0]["Приготовление:"]
        return (
            f"🍹 {drink_name}\n\n"
            f"Ингредиенты:\n{ingredients}\n\n"
            f"Приготовление:\n{preparation}"
        )
