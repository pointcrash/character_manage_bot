import os
from dotenv import load_dotenv
from aiogram.fsm.state import State, StatesGroup

# Загрузка переменных окружения
load_dotenv()

# Настройки бота
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Состояния FSM для создания персонажа
class CharacterCreation(StatesGroup):
    waiting_for_name = State()
    waiting_for_race = State()
    waiting_for_class = State()
    waiting_for_level = State()
    waiting_for_abilities = State()

# Состояния FSM для управления персонажами
class CharacterManagement(StatesGroup):
    waiting_for_character_select = State()
    waiting_for_delete_confirmation = State()
    waiting_for_delete_answer = State()
    waiting_for_proficiencies_character = State()
    waiting_for_proficiencies_list = State()
    waiting_for_expertise_character = State()
    waiting_for_expertise_list = State()
    waiting_for_saving_throws_character = State()
    waiting_for_saving_throws_list = State()

# Доступные расы и классы
RACES = [
    "Человек", "Эльф", "Дварф", "Полурослик", "Полуэльф", 
    "Полуорк", "Тифлинг", "Гном", "Драконорожденный"
]

CLASSES = [
    "Варвар", "Бард", "Жрец", "Друид", "Воин", 
    "Монах", "Паладин", "Следопыт", "Плут", 
    "Чародей", "Колдун", "Волшебник"
]

# Сообщения бота
MESSAGES = {
    "start": (
        "Привет! Я бот для управления персонажами D&D 5e. "
        "Я помогу тебе создать и управлять своим персонажем.\n\n"
        "Используй /help чтобы узнать, что я умею!"
    ),
    "help": (
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/create_character - Создать нового персонажа\n"
        "/list_characters - Показать список персонажей\n"
        "/view_character - Просмотреть информацию о персонаже\n"
        "/delete_character - Удалить персонажа"
    ),
    "character_creation": {
        "start": "Давайте создадим нового персонажа! Как его зовут?",
        "name_invalid": "Имя персонажа должно содержать от 2 до 30 символов. Попробуйте еще раз:",
        "race": "Выберите расу персонажа:",
        "class": "Выберите класс персонажа:",
        "level": "Укажите уровень персонажа (от 1 до 20):",
        "level_invalid": "Уровень должен быть числом от 1 до 20. Попробуйте еще раз:",
        "abilities": (
            "Теперь распределите характеристики персонажа.\n"
            "Введите 6 чисел через пробел (от 3 до 18).\n"
            "Порядок: Сила, Ловкость, Телосложение, Интеллект, Мудрость, Харизма\n"
            "Например: 15 14 13 12 10 8"
        ),
        "abilities_invalid": (
            "Пожалуйста, введите 6 чисел от 3 до 18 через пробел.\n"
            "Порядок: Сила, Ловкость, Телосложение, Интеллект, Мудрость, Харизма"
        ),
        "success": "Отлично! Персонаж успешно создан! Используйте /help для просмотра доступных команд."
    },
    "character_management": {
        "no_characters": "У вас пока нет созданных персонажей. Используйте /create_character чтобы создать первого персонажа!",
        "list_characters": "Ваши персонажи:\n\n{characters_list}",
        "select_character": "Выберите персонажа:",
        "character_info": (
            "📋 Информация о персонаже:\n\n"
            "👤 Имя: {name}\n"
            "🏃 Раса: {race}\n"
            "⚔️ Класс: {class_name}\n"
            "📊 Уровень: {level}\n\n"
            "📈 Характеристики:\n"
            "💪 Сила: {strength} ({strength_mod:+d})\n"
            "🎯 Ловкость: {dexterity} ({dexterity_mod:+d})\n"
            "❤️ Телосложение: {constitution} ({constitution_mod:+d})\n"
            "🧠 Интеллект: {intelligence} ({intelligence_mod:+d})\n"
            "👁️ Мудрость: {wisdom} ({wisdom_mod:+d})\n"
            "✨ Харизма: {charisma} ({charisma_mod:+d})"
        ),
        "delete_confirmation": "Вы уверены, что хотите удалить персонажа {name}? (да/нет)",
        "delete_success": "Персонаж {name} успешно удален.",
        "delete_cancelled": "Удаление персонажа отменено."
    },
    "common": {
        "invalid_input": "Пожалуйста, используйте кнопки для выбора.",
        "error": "Произошла ошибка. Пожалуйста, попробуйте позже."
    }
} 