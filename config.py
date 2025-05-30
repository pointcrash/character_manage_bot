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
    waiting_for_hit_points_character = State()
    waiting_for_hit_points_value = State()
    waiting_for_armor_class_character = State()
    waiting_for_armor_class_value = State()
    waiting_for_speed_character = State()
    waiting_for_speed_value = State()
    waiting_for_proficiency_bonus_character = State()
    waiting_for_proficiency_bonus_value = State()
    waiting_for_edit_character = State()
    waiting_for_edit_name = State()
    waiting_for_edit_race = State()
    waiting_for_edit_class = State()
    waiting_for_edit_level = State()
    # Состояния для управления заклинаниями
    waiting_for_spell_slots_character = State()
    waiting_for_spell_slots_values = State()
    waiting_for_add_spell_character = State()
    waiting_for_spell_type = State()
    waiting_for_spell_level = State()
    waiting_for_spell_name = State()
    waiting_for_remove_spell_character = State()
    waiting_for_remove_spell_type = State()
    waiting_for_remove_spell_name = State()
    waiting_for_view_spells_character = State()
    # Состояния для управления деньгами
    waiting_for_money_character = State()
    waiting_for_money_operation = State()
    waiting_for_money_amount = State()
    # Состояния для управления инвентарем
    waiting_for_inventory_character = State()
    waiting_for_inventory_operation = State()
    waiting_for_inventory_category = State()
    waiting_for_inventory_item_name = State()
    waiting_for_inventory_item_remove = State()
    # Состояния для управления описанием
    waiting_for_description_character = State()
    waiting_for_description_text = State()
    waiting_for_view_description_character = State()
    # Состояния для управления снаряжением
    waiting_for_view_equipment_character = State()
    # Состояния для управления активным персонажем
    waiting_for_active_character = State()

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
    "start": "Добро пожаловать в бота для управления персонажами D&D!",
    "help": """Доступные команды:

Основные команды:
/help - Показать это сообщение
/create_character - Создать нового персонажа
/list_characters - Показать список персонажей
/view_character - Просмотреть информацию о персонаже
/edit_character - Редактировать базовые параметры персонажа
/delete_character - Удалить персонажа

Управление снаряжением:
/view_equipment - Просмотреть снаряжение персонажа
/set_money - Управление деньгами персонажа
/inventory - Управление инвентарем персонажа

Управление навыками и спасбросками:
/set_proficiencies - Установить владение навыками
/set_expertise - Установить компетенцию навыков
/set_saving_throws - Установить владение спасбросками

Управление базовыми параметрами:
/set_hit_points - Установить здоровье
/set_armor_class - Установить класс брони
/set_speed - Установить скорость
/set_proficiency_bonus - Установить бонус мастерства
/set_description - Установить описание персонажа
/view_description - Просмотреть описание персонажа

Управление заклинаниями:
/view_spells - Просмотреть магические способности персонажа
/set_spell_slots - Установить ячейки заклинаний
/add_spell - Добавить заклинание или заговор
/remove_spell - Удалить заклинание или заговор

Управление активным персонажем:
/set_active - Выбрать активного персонажа
/get_active - Показать текущего активного персонажа""",

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