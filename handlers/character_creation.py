from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from config import (
    MESSAGES, CharacterCreation,
    RACES, CLASSES
)
from storage.character_storage import CharacterStorage

# Инициализация хранилища
character_storage = CharacterStorage()

def calculate_modifier(ability_score: int) -> int:
    """Рассчитать модификатор характеристики"""
    return (ability_score - 10) // 2

def calculate_skill_values(abilities: dict, proficiency_bonus: int, proficiencies: list, expertise: list) -> dict:
    """Рассчитать значения всех навыков"""
    skill_values = {}
    
    # Проходим по всем характеристикам и их навыкам
    for ability, data in abilities.items():
        ability_modifier = data['modifier']
        
        # Для каждого навыка этой характеристики
        for skill in data['skills']:
            # Базовое значение - модификатор характеристики
            value = ability_modifier
            
            # Добавляем бонус мастерства если навык в списке мастерства
            if skill in proficiencies:
                value += proficiency_bonus
            
            # Удваиваем бонус мастерства если навык в списке экспертизы
            if skill in expertise:
                value += proficiency_bonus
            
            skill_values[skill] = value
    
    return skill_values

def calculate_saving_throw_value(character: dict, ability: str) -> int:
    """Рассчитать значение спасброска с учетом модификатора характеристики и бонуса мастерства"""
    # Получаем модификатор характеристики
    ability_modifier = character['abilities'][ability]['modifier']
    
    # Получаем бонус мастерства
    proficiency_bonus = character['base_stats']['proficiency_bonus']['value']
    
    # Базовое значение - модификатор характеристики
    value = ability_modifier
    
    # Добавляем бонус мастерства если спасбросок в списке мастерства
    if character['abilities'][ability]['saving_throw_proficient']:
        value += proficiency_bonus
    
    return value

# Обработчик команды /create_character
async def cmd_create_character(message: types.Message, state: FSMContext):
    await message.answer(MESSAGES["character_creation"]["start"])
    await state.set_state(CharacterCreation.waiting_for_name)

# Обработчик ввода имени
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if not 2 <= len(name) <= 30:
        await message.answer(MESSAGES["character_creation"]["name_invalid"])
        return
    
    # Проверяем, не существует ли уже персонаж с таким именем
    existing_character = character_storage.load_character(message.from_user.id, name)
    if existing_character:
        await message.answer("У вас уже есть персонаж с таким именем. Пожалуйста, выберите другое имя.")
        return
    
    await state.update_data(name=name)
    
    # Создаем клавиатуру с расами
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=race)] for race in RACES],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        MESSAGES["character_creation"]["race"],
        reply_markup=keyboard
    )
    await state.set_state(CharacterCreation.waiting_for_race)

# Обработчик выбора расы
async def process_race(message: types.Message, state: FSMContext):
    race = message.text.strip()
    if race not in RACES:
        await message.answer("Пожалуйста, выберите расу из списка.")
        return
    
    await state.update_data(race=race)
    
    # Создаем клавиатуру с классами
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=class_name)] for class_name in CLASSES],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        MESSAGES["character_creation"]["class"],
        reply_markup=keyboard
    )
    await state.set_state(CharacterCreation.waiting_for_class)

# Обработчик выбора класса
async def process_class(message: types.Message, state: FSMContext):
    class_name = message.text.strip()
    if class_name not in CLASSES:
        await message.answer("Пожалуйста, выберите класс из списка.")
        return
    
    await state.update_data(class_name=class_name)
    
    await message.answer(
        MESSAGES["character_creation"]["level"],
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CharacterCreation.waiting_for_level)

# Обработчик ввода уровня
async def process_level(message: types.Message, state: FSMContext):
    try:
        level = int(message.text.strip())
        if not 1 <= level <= 20:
            await message.answer(MESSAGES["character_creation"]["level_invalid"])
            return
    except ValueError:
        await message.answer(MESSAGES["character_creation"]["level_invalid"])
        return
    
    await state.update_data(level=level)
    
    await message.answer(MESSAGES["character_creation"]["abilities"])
    await state.set_state(CharacterCreation.waiting_for_abilities)

# Обработчик ввода характеристик
async def process_abilities(message: types.Message, state: FSMContext):
    try:
        abilities = [int(x) for x in message.text.strip().split()]
        if len(abilities) != 6 or not all(3 <= x <= 18 for x in abilities):
            await message.answer(MESSAGES["character_creation"]["abilities_invalid"])
            return
    except ValueError:
        await message.answer(MESSAGES["character_creation"]["abilities_invalid"])
        return
    
    # Получаем все данные персонажа
    character_data = await state.get_data()
    
    # Создаем структуру персонажа в формате character_stats
    character = {
        "name": character_data["name"],
        "race": character_data["race"],
        "class_name": character_data["class_name"],
        "level": character_data["level"],
        "user_id": message.from_user.id,
        "abilities": {
            "strength": {
                "name": "Сила",
                "description": "Физическая сила и атлетические способности",
                "skills": ["Атлетика"],
                "value": abilities[0],
                "modifier": (abilities[0] - 10) // 2,
                "saving_throw_proficient": False
            },
            "dexterity": {
                "name": "Ловкость",
                "description": "Координация, рефлексы и равновесие",
                "skills": ["Акробатика", "Ловкость рук", "Скрытность"],
                "value": abilities[1],
                "modifier": (abilities[1] - 10) // 2,
                "saving_throw_proficient": False
            },
            "constitution": {
                "name": "Телосложение",
                "description": "Здоровье, выносливость и жизненная сила",
                "skills": [],
                "value": abilities[2],
                "modifier": (abilities[2] - 10) // 2,
                "saving_throw_proficient": False
            },
            "intelligence": {
                "name": "Интеллект",
                "description": "Умственные способности, память и логика",
                "skills": ["Анализ", "История", "Магия", "Природа", "Религия"],
                "value": abilities[3],
                "modifier": (abilities[3] - 10) // 2,
                "saving_throw_proficient": False
            },
            "wisdom": {
                "name": "Мудрость",
                "description": "Восприятие, интуиция и проницательность",
                "skills": ["Восприятие", "Выживание", "Медицина", "Проницательность", "Уход за животными"],
                "value": abilities[4],
                "modifier": (abilities[4] - 10) // 2,
                "saving_throw_proficient": False
            },
            "charisma": {
                "name": "Харизма",
                "description": "Сила личности, убеждение и лидерство",
                "skills": ["Запугивание", "Обман", "Убеждение", "Выступление"],
                "value": abilities[5],
                "modifier": (abilities[5] - 10) // 2,
                "saving_throw_proficient": False
            }
        },
        "base_stats": {
            "hit_points": {
                "name": "Хиты",
                "description": "Количество очков здоровья",
                "maximum": 0,
                "current": 0,
                "temporary": 0
            },
            "armor_class": {
                "name": "Класс брони",
                "description": "Защита от атак",
                "value": 10,
                "base": 10,
                "bonus": 0
            },
            "proficiency_bonus": {
                "name": "Бонус мастерства",
                "description": "Бонус к проверкам характеристик и атакам",
                "value": 2
            },
            "speed": {
                "name": "Скорость",
                "description": "Базовая скорость передвижения",
                "base": 30,
                "current": 30,
                "fly": 0,
                "swim": 0,
                "climb": 0,
                "burrow": 0
            }
        },
        "advanced_stats": {
            "saving_throws": {
                "name": "Спасброски",
                "description": "Базовые спасброски по характеристикам",
                "values": {
                    "strength": 0,
                    "dexterity": 0,
                    "constitution": 0,
                    "intelligence": 0,
                    "wisdom": 0,
                    "charisma": 0
                }
            },
            "skills": {
                "name": "Навыки",
                "description": "Все доступные навыки персонажа",
                "proficiencies": [],
                "expertise": [],
                "values": {}
            },
            "resistances": {
                "name": "Сопротивления",
                "description": "Сопротивление к различным типам урона",
                "values": []
            },
            "immunities": {
                "name": "Иммунитеты",
                "description": "Иммунитеты к различным эффектам",
                "values": []
            }
        },
        "equipment": {
            "weapons": {
                "name": "Оружие",
                "description": "Вооружение персонажа",
                "items": []
            },
            "armor": {
                "name": "Броня",
                "description": "Защитное снаряжение",
                "items": []
            },
            "items": {
                "name": "Предметы",
                "description": "Различные предметы в инвентаре",
                "items": []
            },
            "money": {
                "name": "Деньги",
                "description": "Валюта и ценности",
                "copper": 0,
                "silver": 0,
                "gold": 0,
                "platinum": 0
            }
        },
        "magic": {
            "spell_slots": {
                "name": "Ячейки заклинаний",
                "description": "Доступные ячейки для заклинаний",
                "values": {
                    "1": 0,
                    "2": 0,
                    "3": 0,
                    "4": 0,
                    "5": 0,
                    "6": 0,
                    "7": 0,
                    "8": 0,
                    "9": 0
                }
            },
            "spells_known": {
                "name": "Известные заклинания",
                "description": "Список известных заклинаний",
                "cantrips": [],
                "spells": []
            },
            "spell_save_dc": {
                "name": "Сложность спасброска",
                "description": "Сложность спасброска от заклинаний",
                "value": 0
            },
            "spell_attack_bonus": {
                "name": "Бонус к атаке заклинаниями",
                "description": "Бонус к броскам атаки заклинаниями",
                "value": 0
            }
        }
    }
    
    # Рассчитываем значения навыков
    skill_values = calculate_skill_values(
        character['abilities'],
        character['base_stats']['proficiency_bonus']['value'],
        character['advanced_stats']['skills']['proficiencies'],
        character['advanced_stats']['skills']['expertise']
    )
    
    # Обновляем значения навыков в структуре персонажа
    character['advanced_stats']['skills']['values'] = skill_values
    
    # Рассчитываем значения спасбросков
    for ability in character['abilities']:
        character['advanced_stats']['saving_throws']['values'][ability] = calculate_saving_throw_value(character, ability)
    
    # Сохраняем персонажа
    if character_storage.save_character(message.from_user.id, character):
        await message.answer(MESSAGES["character_creation"]["success"])
    else:
        await message.answer("Произошла ошибка при сохранении персонажа. Пожалуйста, попробуйте позже.")
    
    await state.clear()

def register_character_creation_handlers(dp):
    """Регистрация всех обработчиков создания персонажа"""
    dp.message.register(cmd_create_character, Command("create_character"))
    dp.message.register(process_name, CharacterCreation.waiting_for_name)
    dp.message.register(process_race, CharacterCreation.waiting_for_race)
    dp.message.register(process_class, CharacterCreation.waiting_for_class)
    dp.message.register(process_level, CharacterCreation.waiting_for_level)
    dp.message.register(process_abilities, CharacterCreation.waiting_for_abilities) 