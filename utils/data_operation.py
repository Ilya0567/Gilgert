import pandas as pd
from .config import DATA_FILE, PRODUCT_PATH
from random import randint

from natasha import MorphVocab, NewsEmbedding, NewsMorphTagger, Doc, Segmenter

def id_request():
    """
    функция для генерации уникального id

    Returns:
        str: Сгенерированный уникальный номер сообщения.
    """
    return "".join([str(randint(0, 10)) for i in range(7)])


def save_user_data(timestamp, username, question, answer) -> str:
    """
    функция для сохранения вопросов от пользователей

    Args:
        timestamp (timestamp): время в формате timestamp
        username (int): id пользователя
        question (str): вопрос от пользователя
        answer (str): ответ на вопрос
    Returns:
        str: Уникальный номер сообщения.
    """
    # генерируем уникальный номер сообщения
    id = id_request()
    
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

def load_products() -> pd.DataFrame:
    """
    Загружает продукты из CSV файла.

    Returns:
        pd.DataFrame: Датафрейм с продуктами.
    """
    return pd.read_csv(PRODUCT_PATH)

def initialize_nlp() -> tuple:
    """
    Инициализирует NLP компоненты из библиотеки Natasha.

    Returns:
        tuple: Кортеж из инициализированных объектов (Segmenter, NewsEmbedding, NewsMorphTagger, MorphVocab).
    """
    segmenter = Segmenter()
    emb = NewsEmbedding()
    morph_tagger = NewsMorphTagger(emb)
    morph_vocab = MorphVocab()
    return segmenter, emb, morph_tagger, morph_vocab

# Инициализируем NLP компоненты
segmenter, emb, morph_tagger, morph_vocab = initialize_nlp()

def lemmatize_word(word: str) -> str:
    """
    Приводит слово к его лемматизированной форме.

    Args:
        word (str): Слово для лемматизации.

    Returns:
        str: Лемматизированное слово или None, если токенизация не удалась.
    """
    doc = Doc(word)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    if doc.tokens:
        lemmatized = [token.lemmatize(morph_vocab) for token in doc.tokens]
        return " ".join([token.lemma for token in doc.tokens])
    return None  # Если токенизация не удалась

# Загружаем продукты
products = load_products()

def check_product(product: str) -> str:
    """
    Проверяет, можно ли есть указанный продукт.

    Args:
        product (str): Название продукта.

    Returns:
        str: Сообщение с рекомендацией по употреблению продукта.
    """
    recommended = products['РЕКОМЕНДОВАНО']
    avoid = products['ИЗБЕГАТЬ']
    
    product = lemmatize_word(product)  # Приводим слово в начальную форму
    
    in_recommended = any(product in item for item in recommended)
    in_avoid = any(product in item for item in avoid)
    

    if in_recommended and not in_avoid:
        return (
            "✅ *Этот продукт можно есть.*\n"
            "Вы можете спокойно употреблять этот продукт в пищу."
        )
    elif in_avoid and not in_recommended:
        return (
            "❌ *Этот продукт нельзя есть.*\n"
            "К сожалению, этот продукт находится в списке нерекомендуемых."
        )
    elif in_recommended and in_avoid:
        return (
            "⚠️ *Этот продукт есть как в списке рекомендованных, так и в списке запрещённых.*\n"
            "Поэтому вопрос передан нашим специалистам, от которых я скоро принесу Вам ответ."
        )
    else:
        return (
            "❓ *Я не нашел информацию по этому продукту.*\n"
            "Поэтому передал вопрос нашим специалистам, от которых я скоро принесу Вам ответ."
        )
