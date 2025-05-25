from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from config import MESSAGES, CharacterManagement, RACES, CLASSES
from storage.character_storage import CharacterStorage

# Инициализация хранилища
character_storage = CharacterStorage()

def calculate_modifier(ability_score: int) -> int:
    """Рассчитать модификатор характеристики"""
    return (ability_score - 10) // 2

def calculate_skill_value(character: dict, skill: str) -> int:
    """Рассчитать значение навыка с учетом модификатора характеристики и бонуса мастерства"""
    # Находим характеристику, от которой зависит навык
    ability = None
    for abil, data in character['abilities'].items():
        if skill in data['skills']:
            ability = abil
            break
    
    if ability is None:
        return 0
    
    # Получаем модификатор характеристики
    ability_modifier = character['abilities'][ability]['modifier']
    
    # Получаем бонус мастерства
    proficiency_bonus = character['base_stats']['proficiency_bonus']['value']
    
    # Базовое значение - модификатор характеристики
    value = ability_modifier
    
    # Добавляем бонус мастерства если навык в списке мастерства
    if skill in character['advanced_stats']['skills']['proficiencies']:
        value += proficiency_bonus
    
    # Добавляем дополнительный бонус мастерства если навык в списке экспертизы
    if skill in character['advanced_stats']['skills']['expertise']:
        value += proficiency_bonus * 2
    
    return value

def get_all_skills(character: dict) -> list:
    """Получить список всех доступных навыков персонажа"""
    skills = []
    for ability_data in character['abilities'].values():
        skills.extend(ability_data['skills'])
    return skills

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

# Обработчик команды /list_characters
async def cmd_list_characters(message: types.Message):
    characters = character_storage.get_user_characters(message.from_user.id)
    
    if not characters:
        await message.answer(MESSAGES["character_management"]["no_characters"])
        return
    
    characters_list = "\n".join(
        f"👤 {char['name']} - {char['race']} {char['class_name']} {char['level']} уровня"
        for char in characters
    )
    
    await message.answer(
        MESSAGES["character_management"]["list_characters"].format(
            characters_list=characters_list
        )
    )

# Обработчик команды /view_character
async def cmd_view_character(message: types.Message, state: FSMContext):
    characters = character_storage.get_user_characters(message.from_user.id)
    
    if not characters:
        await message.answer(MESSAGES["character_management"]["no_characters"])
        return
    
    # Создаем клавиатуру с персонажами
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=char["name"])] for char in characters],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        MESSAGES["character_management"]["select_character"],
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_character_select)

# Обработчик выбора персонажа для просмотра
async def process_character_select(message: types.Message, state: FSMContext):
    character_name = message.text.strip()
    character = character_storage.load_character(message.from_user.id, character_name)
    
    if not character:
        await message.answer(
            MESSAGES["common"]["invalid_input"],
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    # Формируем сообщение с информацией о персонаже
    character_info = (
        f"👤 {character['name']}\n"
        f"Раса: {character['race']}\n"
        f"Класс: {character['class_name']}\n"
        f"Уровень: {character['level']}\n\n"
        f"Характеристики:\n"
    )
    
    # Добавляем информацию о характеристиках
    for ability, data in character['abilities'].items():
        character_info += (
            f"{data['name']}: {data['value']} "
            f"(модификатор: {data['modifier']:+d})\n"
        )
    
    # Добавляем базовые параметры
    character_info += f"\nБазовые параметры:\n"
    character_info += f"Хиты: {character['base_stats']['hit_points']['current']}/{character['base_stats']['hit_points']['maximum']}\n"
    character_info += f"Класс брони: {character['base_stats']['armor_class']['value']}\n"
    character_info += f"Бонус мастерства: +{character['base_stats']['proficiency_bonus']['value']}\n"
    character_info += f"Скорость: {character['base_stats']['speed']['current']} футов\n"
    
    # Добавляем информацию о спасбросках
    character_info += f"\nСпасброски:\n"
    for ability, data in character['abilities'].items():
        value = character['advanced_stats']['saving_throws']['values'][ability]
        if data['saving_throw_proficient']:
            character_info += f"  {data['name']}: {value:+d} ✓\n"
        else:
            character_info += f"  {data['name']}: {value:+d}\n"
    
    # Добавляем информацию о навыках
    character_info += f"\nНавыки:\n"
    proficiencies = character['advanced_stats']['skills']['proficiencies']
    expertise = character['advanced_stats']['skills']['expertise']
    
    for skill, _ in character['advanced_stats']['skills']['values'].items():
        value = calculate_skill_value(character, skill)
        if skill in expertise:
            character_info += f"  {skill}: {value:+d} ✓✓\n"
        elif skill in proficiencies:
            character_info += f"  {skill}: {value:+d} ✓\n"
        else:
            character_info += f"  {skill}: {value:+d}\n"
    
    # Добавляем информацию о сопротивлениях и иммунитетах
    if character['advanced_stats']['resistances']['values'] or character['advanced_stats']['immunities']['values']:
        character_info += f"\nОсобые способности:\n"
        if character['advanced_stats']['resistances']['values']:
            character_info += f"Сопротивления:\n"
            for resistance in character['advanced_stats']['resistances']['values']:
                character_info += f"  • {resistance}\n"
        if character['advanced_stats']['immunities']['values']:
            character_info += f"Иммунитеты:\n"
            for immunity in character['advanced_stats']['immunities']['values']:
                character_info += f"  • {immunity}\n"
    
    # Добавляем описание персонажа, если оно есть
    if character.get('description'):
        character_info += f"\n📝 Описание:\n{character['description']}\n"
    
    await message.answer(
        character_info,
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()

# Обработчик команды /delete_character
async def cmd_delete_character(message: types.Message, state: FSMContext):
    characters = character_storage.get_user_characters(message.from_user.id)
    
    if not characters:
        await message.answer(MESSAGES["character_management"]["no_characters"])
        return
    
    # Создаем клавиатуру с персонажами
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=char["name"])] for char in characters],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        MESSAGES["character_management"]["select_character"],
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_delete_confirmation)

# Обработчик подтверждения удаления
async def process_delete_confirmation(message: types.Message, state: FSMContext):
    character_name = message.text.strip()
    character = character_storage.load_character(message.from_user.id, character_name)
    
    if not character:
        await message.answer(
            MESSAGES["common"]["invalid_input"],
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    # Создаем клавиатуру с подтверждением
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="да"), KeyboardButton(text="нет")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        MESSAGES["character_management"]["delete_confirmation"].format(
            name=character_name
        ),
        reply_markup=keyboard
    )
    await state.update_data(character_name=character_name)
    await state.set_state(CharacterManagement.waiting_for_delete_answer)

# Обработчик ответа на подтверждение удаления
async def process_delete_answer(message: types.Message, state: FSMContext):
    answer = message.text.strip().lower()
    data = await state.get_data()
    character_name = data["character_name"]
    
    if answer == "да":
        if character_storage.delete_character(message.from_user.id, character_name):
            await message.answer(
                MESSAGES["character_management"]["delete_success"].format(
                    name=character_name
                ),
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await message.answer(
                MESSAGES["common"]["error"],
                reply_markup=ReplyKeyboardRemove()
            )
    else:
        await message.answer(
            MESSAGES["character_management"]["delete_cancelled"],
            reply_markup=ReplyKeyboardRemove()
        )
    
    await state.clear()

# Обработчик команды /set_proficiencies
async def cmd_set_proficiencies(message: types.Message, state: FSMContext):
    characters = character_storage.get_user_characters(message.from_user.id)
    
    if not characters:
        await message.answer(MESSAGES["character_management"]["no_characters"])
        return
    
    # Создаем клавиатуру с персонажами
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=char["name"])] for char in characters],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        "Выберите персонажа для установки мастерства навыков:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_proficiencies_character)

# Обработчик выбора персонажа для установки мастерства
async def process_proficiencies_character(message: types.Message, state: FSMContext):
    character_name = message.text.strip()
    character = character_storage.load_character(message.from_user.id, character_name)
    
    if not character:
        await message.answer(
            MESSAGES["common"]["invalid_input"],
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    # Сохраняем имя персонажа в состоянии
    await state.update_data(character_name=character_name)
    
    # Получаем список всех доступных навыков
    all_skills = get_all_skills(character)
    
    # Получаем текущие выбранные навыки
    current_proficiencies = character['advanced_stats']['skills']['proficiencies']
    
    await message.answer(
        f"Введите названия навыков через запятую для установки мастерства.\n"
        f"Например: Уход за животными, Атлетика, Скрытность\n\n"
        f"Текущие навыки с мастерством:\n"
        f"{', '.join(current_proficiencies) if current_proficiencies else 'Нет'}\n\n"
        f"Примечание: повторный ввод навыка снимет с него мастерство.\n\n"
        f"Доступные навыки: {', '.join(all_skills)}",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CharacterManagement.waiting_for_proficiencies_list)

# Обработчик ввода списка навыков для мастерства
async def process_proficiencies_list(message: types.Message, state: FSMContext):
    data = await state.get_data()
    character_name = data["character_name"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    # Получаем список всех доступных навыков
    all_skills = get_all_skills(character)
    
    # Разбиваем введенный текст на навыки по запятым, сохраняя пробелы внутри названий
    input_skills = [skill.strip() for skill in message.text.split(',')]
    
    # Создаем словарь для поиска навыков без учета регистра
    skills_lower = {skill.lower(): skill for skill in all_skills}
    
    # Проверяем валидность навыков и приводим их к правильному регистру
    normalized_skills = []
    invalid_skills = []
    
    for skill in input_skills:
        skill_lower = skill.lower()
        if skill_lower in skills_lower:
            normalized_skills.append(skills_lower[skill_lower])
        else:
            invalid_skills.append(skill)
    
    if invalid_skills:
        await message.answer(
            f"Следующие навыки не найдены: {', '.join(invalid_skills)}\n"
            f"Пожалуйста, используйте только доступные навыки: {', '.join(all_skills)}\n\n"
            f"Введите навыки через запятую, например:\n"
            f"Уход за животными, Атлетика, Скрытность"
        )
        return
    
    # Удаляем навыки из списка если они там есть
    character['advanced_stats']['skills']['proficiencies'] = list(
        set(character['advanced_stats']['skills']['proficiencies']) ^ set(normalized_skills))
    
    # Удаляем навыки из списка экспертизы, если они там есть
    character['advanced_stats']['skills']['expertise'] = [
        skill for skill in character['advanced_stats']['skills']['expertise']
        if skill not in normalized_skills
    ]
    
    # Пересчитываем значения навыков
    skill_values = {}
    for skill in all_skills:
        skill_values[skill] = calculate_skill_value(character, skill)
    character['advanced_stats']['skills']['values'] = skill_values
    
    # Сохраняем изменения
    if character_storage.save_character(message.from_user.id, character):
        await message.answer("Мастерство навыков успешно обновлено!")
    else:
        await message.answer("Произошла ошибка при сохранении изменений.")
    
    await state.clear()

# Обработчик команды /set_expertise
async def cmd_set_expertise(message: types.Message, state: FSMContext):
    characters = character_storage.get_user_characters(message.from_user.id)
    
    if not characters:
        await message.answer(MESSAGES["character_management"]["no_characters"])
        return
    
    # Создаем клавиатуру с персонажами
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=char["name"])] for char in characters],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        "Выберите персонажа для установки экспертизы навыков:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_expertise_character)

# Обработчик выбора персонажа для установки экспертизы
async def process_expertise_character(message: types.Message, state: FSMContext):
    character_name = message.text.strip()
    character = character_storage.load_character(message.from_user.id, character_name)
    
    if not character:
        await message.answer(
            MESSAGES["common"]["invalid_input"],
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    # Сохраняем имя персонажа в состоянии
    await state.update_data(character_name=character_name)
    
    # Получаем список всех доступных навыков
    all_skills = get_all_skills(character)
    
    await message.answer(
        f"Введите названия навыков через пробел для установки экспертизы.\n"
        f"Доступные навыки: {', '.join(all_skills)}",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CharacterManagement.waiting_for_expertise_list)

# Обработчик ввода списка навыков для экспертизы
async def process_expertise_list(message: types.Message, state: FSMContext):
    data = await state.get_data()
    character_name = data["character_name"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    # Получаем список всех доступных навыков
    all_skills = get_all_skills(character)
    
    # Разбиваем введенный текст на навыки
    input_skills = [skill.strip() for skill in message.text.split()]
    
    # Проверяем валидность навыков
    invalid_skills = [skill for skill in input_skills if skill not in all_skills]
    if invalid_skills:
        await message.answer(
            f"Следующие навыки не найдены: {', '.join(invalid_skills)}\n"
            f"Пожалуйста, используйте только доступные навыки: {', '.join(all_skills)}"
        )
        return
    
    # Удаляем навыки из списка если они там есть
    character['advanced_stats']['skills']['expertise'] = list(
        set(character['advanced_stats']['skills']['expertise']) ^ set(input_skills))
    
    # Удаляем навыки из списка мастерства, если они там есть
    character['advanced_stats']['skills']['proficiencies'] = [
        skill for skill in character['advanced_stats']['skills']['proficiencies']
        if skill not in input_skills
    ]
    
    # Пересчитываем значения навыков
    skill_values = {}
    for skill in all_skills:
        skill_values[skill] = calculate_skill_value(character, skill)
    character['advanced_stats']['skills']['values'] = skill_values
    
    # Сохраняем изменения
    if character_storage.save_character(message.from_user.id, character):
        await message.answer("Экспертиза навыков успешно обновлена!")
    else:
        await message.answer("Произошла ошибка при сохранении изменений.")
    
    await state.clear()

# Обработчик команды /set_saving_throws
async def cmd_set_saving_throws(message: types.Message, state: FSMContext):
    characters = character_storage.get_user_characters(message.from_user.id)
    
    if not characters:
        await message.answer(MESSAGES["character_management"]["no_characters"])
        return
    
    # Создаем клавиатуру с персонажами
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=char["name"])] for char in characters],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        "Выберите персонажа для установки владения спасбросками:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_saving_throws_character)

# Обработчик выбора персонажа для установки спасбросков
async def process_saving_throws_character(message: types.Message, state: FSMContext):
    character_name = message.text.strip()
    character = character_storage.load_character(message.from_user.id, character_name)
    
    if not character:
        await message.answer(
            MESSAGES["common"]["invalid_input"],
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    # Сохраняем имя персонажа в состоянии
    await state.update_data(character_name=character_name)
    
    # Получаем список всех характеристик
    abilities = [data['name'] for data in character['abilities'].values()]
    
    await message.answer(
        f"Введите названия характеристик через пробел для установки владения спасбросками.\n"
        f"Доступные характеристики: {', '.join(abilities)}",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CharacterManagement.waiting_for_saving_throws_list)

# Обработчик ввода списка характеристик для спасбросков
async def process_saving_throws_list(message: types.Message, state: FSMContext):
    data = await state.get_data()
    character_name = data["character_name"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    # Получаем список всех характеристик
    abilities = {data['name']: ability for ability, data in character['abilities'].items()}
    
    # Разбиваем введенный текст на характеристики
    input_abilities = [ability.strip() for ability in message.text.split()]
    
    # Проверяем валидность характеристик
    invalid_abilities = [ability for ability in input_abilities if ability not in abilities]
    if invalid_abilities:
        await message.answer(
            f"Следующие характеристики не найдены: {', '.join(invalid_abilities)}\n"
            f"Пожалуйста, используйте только доступные характеристики: {', '.join(abilities.keys())}"
        )
        return
    
    # Сбрасываем все спасброски
    for ability in character['abilities'].values():
        ability['saving_throw_proficient'] = False
    
    # Устанавливаем владение для выбранных характеристик
    for ability_name in input_abilities:
        ability_key = abilities[ability_name]
        character['abilities'][ability_key]['saving_throw_proficient'] = True
    
    # Обновляем значения всех спасбросков
    for ability in character['abilities']:
        character['advanced_stats']['saving_throws']['values'][ability] = calculate_saving_throw_value(character, ability)
    
    # Сохраняем изменения
    if character_storage.save_character(message.from_user.id, character):
        await message.answer("Владение спасбросками успешно обновлено!")
    else:
        await message.answer("Произошла ошибка при сохранении изменений.")
    
    await state.clear()

# Обработчик команды /set_hit_points
async def cmd_set_hit_points(message: types.Message, state: FSMContext):
    characters = character_storage.get_user_characters(message.from_user.id)
    
    if not characters:
        await message.answer(MESSAGES["character_management"]["no_characters"])
        return
    
    # Создаем клавиатуру с персонажами
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=char["name"])] for char in characters],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        "Выберите персонажа для установки здоровья:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_hit_points_character)

# Обработчик выбора персонажа для установки здоровья
async def process_hit_points_character(message: types.Message, state: FSMContext):
    character_name = message.text.strip()
    character = character_storage.load_character(message.from_user.id, character_name)
    
    if not character:
        await message.answer(
            MESSAGES["common"]["invalid_input"],
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    # Сохраняем имя персонажа в состоянии
    await state.update_data(character_name=character_name)
    
    await message.answer(
        f"Введите значения здоровья через пробел в следующем порядке:\n"
        f"максимальное текущее временное\n"
        f"Например: '20 15 5'\n"
        f"Если ввести только одно число, текущее и временное здоровье будут установлены автоматически\n\n"
        f"Текущие значения:\n"
        f"Максимальное: {character['base_stats']['hit_points']['maximum']}\n"
        f"Текущее: {character['base_stats']['hit_points']['current']}\n"
        f"Временное: {character['base_stats']['hit_points']['temporary']}",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CharacterManagement.waiting_for_hit_points_value)

# Обработчик ввода значения здоровья
async def process_hit_points_value(message: types.Message, state: FSMContext):
    try:
        # Разбиваем ввод на максимальное, текущее и временное здоровье
        values = message.text.strip().split()
        if len(values) > 3:
            await message.answer("Пожалуйста, введите максимум, текущее и временное здоровье через пробел (например: '20 15 5')")
            return
            
        max_hp = int(values[0])
        current_hp = int(values[1]) if len(values) > 1 else max_hp
        temp_hp = int(values[2]) if len(values) > 2 else 0
        
        if max_hp < 0 or current_hp < 0 or temp_hp < 0:
            raise ValueError
            
        # Проверяем, что текущее здоровье не превышает максимальное
        if current_hp > max_hp:
            await message.answer("Текущее здоровье не может быть больше максимального.")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите положительные числа.")
        return
    
    data = await state.get_data()
    character_name = data["character_name"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    # Обновляем значения здоровья
    character['base_stats']['hit_points']['maximum'] = max_hp
    character['base_stats']['hit_points']['current'] = current_hp
    character['base_stats']['hit_points']['temporary'] = temp_hp
    
    # Сохраняем изменения
    if character_storage.save_character(message.from_user.id, character):
        await message.answer(
            f"Здоровье успешно обновлено:\n"
            f"Максимальное: {max_hp}\n"
            f"Текущее: {current_hp}\n"
            f"Временное: {temp_hp}"
        )
    else:
        await message.answer("Произошла ошибка при сохранении изменений.")
    
    await state.clear()

# Обработчик команды /set_armor_class
async def cmd_set_armor_class(message: types.Message, state: FSMContext):
    characters = character_storage.get_user_characters(message.from_user.id)
    
    if not characters:
        await message.answer(MESSAGES["character_management"]["no_characters"])
        return
    
    # Создаем клавиатуру с персонажами
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=char["name"])] for char in characters],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        "Выберите персонажа для установки класса брони:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_armor_class_character)

# Обработчик выбора персонажа для установки класса брони
async def process_armor_class_character(message: types.Message, state: FSMContext):
    character_name = message.text.strip()
    character = character_storage.load_character(message.from_user.id, character_name)
    
    if not character:
        await message.answer(
            MESSAGES["common"]["invalid_input"],
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    # Сохраняем имя персонажа в состоянии
    await state.update_data(character_name=character_name)
    
    await message.answer(
        f"Введите значение класса брони (текущее значение: {character['base_stats']['armor_class']['value']}):",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CharacterManagement.waiting_for_armor_class_value)

# Обработчик ввода значения класса брони
async def process_armor_class_value(message: types.Message, state: FSMContext):
    try:
        armor_class = int(message.text.strip())
        if armor_class < 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите положительное число.")
        return
    
    data = await state.get_data()
    character_name = data["character_name"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    # Обновляем значение класса брони
    character['base_stats']['armor_class']['value'] = armor_class
    
    # Сохраняем изменения
    if character_storage.save_character(message.from_user.id, character):
        await message.answer(f"Класс брони успешно обновлен: {armor_class}")
    else:
        await message.answer("Произошла ошибка при сохранении изменений.")
    
    await state.clear()

# Обработчик команды /set_speed
async def cmd_set_speed(message: types.Message, state: FSMContext):
    characters = character_storage.get_user_characters(message.from_user.id)
    
    if not characters:
        await message.answer(MESSAGES["character_management"]["no_characters"])
        return
    
    # Создаем клавиатуру с персонажами
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=char["name"])] for char in characters],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        "Выберите персонажа для установки скорости:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_speed_character)

# Обработчик выбора персонажа для установки скорости
async def process_speed_character(message: types.Message, state: FSMContext):
    character_name = message.text.strip()
    character = character_storage.load_character(message.from_user.id, character_name)
    
    if not character:
        await message.answer(
            MESSAGES["common"]["invalid_input"],
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    # Сохраняем имя персонажа в состоянии
    await state.update_data(character_name=character_name)
    
    await message.answer(
        f"Введите значения скоростей через пробел в следующем порядке:\n"
        f"обычная полет плавание лазание копание\n"
        f"Например: '30 0 0 0 0'\n\n"
        f"Текущие значения:\n"
        f"Обычная: {character['base_stats']['speed']['current']}\n"
        f"Полет: {character['base_stats']['speed']['fly']}\n"
        f"Плавание: {character['base_stats']['speed']['swim']}\n"
        f"Лазание: {character['base_stats']['speed']['climb']}\n"
        f"Копание: {character['base_stats']['speed']['burrow']}",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CharacterManagement.waiting_for_speed_value)

# Обработчик ввода значения скорости
async def process_speed_value(message: types.Message, state: FSMContext):
    try:
        # Разбиваем ввод на значения скоростей
        values = message.text.strip().split()
        if len(values) != 5:
            await message.answer("Пожалуйста, введите 5 значений скоростей через пробел (обычная полет плавание лазание копание)")
            return
            
        speeds = [int(value) for value in values]
        if any(speed < 0 for speed in speeds):
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите положительные числа.")
        return
    
    data = await state.get_data()
    character_name = data["character_name"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    # Обновляем значения скоростей
    character['base_stats']['speed']['current'] = speeds[0]
    character['base_stats']['speed']['fly'] = speeds[1]
    character['base_stats']['speed']['swim'] = speeds[2]
    character['base_stats']['speed']['climb'] = speeds[3]
    character['base_stats']['speed']['burrow'] = speeds[4]
    
    # Сохраняем изменения
    if character_storage.save_character(message.from_user.id, character):
        await message.answer(
            f"Скорости успешно обновлены:\n"
            f"Обычная: {speeds[0]} футов\n"
            f"Полет: {speeds[1]} футов\n"
            f"Плавание: {speeds[2]} футов\n"
            f"Лазание: {speeds[3]} футов\n"
            f"Копание: {speeds[4]} футов"
        )
    else:
        await message.answer("Произошла ошибка при сохранении изменений.")
    
    await state.clear()

# Обработчик команды /set_proficiency_bonus
async def cmd_set_proficiency_bonus(message: types.Message, state: FSMContext):
    characters = character_storage.get_user_characters(message.from_user.id)
    
    if not characters:
        await message.answer(MESSAGES["character_management"]["no_characters"])
        return
    
    # Создаем клавиатуру с персонажами
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=char["name"])] for char in characters],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        "Выберите персонажа для установки бонуса мастерства:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_proficiency_bonus_character)

# Обработчик выбора персонажа для установки бонуса мастерства
async def process_proficiency_bonus_character(message: types.Message, state: FSMContext):
    character_name = message.text.strip()
    character = character_storage.load_character(message.from_user.id, character_name)
    
    if not character:
        await message.answer(
            MESSAGES["common"]["invalid_input"],
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    # Сохраняем имя персонажа в состоянии
    await state.update_data(character_name=character_name)
    
    await message.answer(
        f"Введите значение бонуса мастерства (текущее значение: +{character['base_stats']['proficiency_bonus']['value']}):",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CharacterManagement.waiting_for_proficiency_bonus_value)

# Обработчик ввода значения бонуса мастерства
async def process_proficiency_bonus_value(message: types.Message, state: FSMContext):
    try:
        bonus = int(message.text.strip())
        if bonus < 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите положительное число.")
        return
    
    data = await state.get_data()
    character_name = data["character_name"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    # Обновляем значение бонуса мастерства
    character['base_stats']['proficiency_bonus']['value'] = bonus
    
    # Пересчитываем значения навыков и спасбросков
    for ability in character['abilities']:
        character['advanced_stats']['saving_throws']['values'][ability] = calculate_saving_throw_value(character, ability)
    
    for skill in character['advanced_stats']['skills']['values']:
        character['advanced_stats']['skills']['values'][skill] = calculate_skill_value(character, skill)
    
    # Сохраняем изменения
    if character_storage.save_character(message.from_user.id, character):
        await message.answer(f"Бонус мастерства успешно обновлен: +{bonus}")
    else:
        await message.answer("Произошла ошибка при сохранении изменений.")
    
    await state.clear()

# Обработчик команды /edit_character
async def cmd_edit_character(message: types.Message, state: FSMContext):
    characters = character_storage.get_user_characters(message.from_user.id)
    
    if not characters:
        await message.answer(MESSAGES["character_management"]["no_characters"])
        return
    
    # Создаем клавиатуру с персонажами
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=char["name"])] for char in characters],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        "Выберите персонажа для редактирования:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_edit_character)

# Обработчик выбора персонажа для редактирования
async def process_edit_character(message: types.Message, state: FSMContext):
    character_name = message.text.strip()
    character = character_storage.load_character(message.from_user.id, character_name)
    
    if not character:
        await message.answer(
            MESSAGES["common"]["invalid_input"],
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    # Сохраняем имя персонажа в состоянии
    await state.update_data(character_name=character_name)
    
    # Создаем клавиатуру с параметрами для редактирования
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Имя"), KeyboardButton(text="Раса")],
            [KeyboardButton(text="Класс"), KeyboardButton(text="Уровень")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        f"Выберите параметр для редактирования:\n"
        f"Текущие значения:\n"
        f"Имя: {character['name']}\n"
        f"Раса: {character['race']}\n"
        f"Класс: {character['class_name']}\n"
        f"Уровень: {character['level']}",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_edit_name)

# Обработчик выбора параметра для редактирования
async def process_edit_parameter(message: types.Message, state: FSMContext):
    parameter = message.text.strip()
    data = await state.get_data()
    character_name = data["character_name"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    if parameter == "Имя":
        await message.answer(
            "Введите новое имя персонажа:",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(CharacterManagement.waiting_for_edit_name)
    elif parameter == "Раса":
        # Создаем клавиатуру с расами
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=race)] for race in RACES],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(
            "Выберите новую расу персонажа:",
            reply_markup=keyboard
        )
        await state.set_state(CharacterManagement.waiting_for_edit_race)
    elif parameter == "Класс":
        # Создаем клавиатуру с классами
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=class_name)] for class_name in CLASSES],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(
            "Выберите новый класс персонажа:",
            reply_markup=keyboard
        )
        await state.set_state(CharacterManagement.waiting_for_edit_class)
    elif parameter == "Уровень":
        await message.answer(
            "Введите новый уровень персонажа (от 1 до 20):",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(CharacterManagement.waiting_for_edit_level)
    else:
        await message.answer(
            MESSAGES["common"]["invalid_input"],
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return

# Обработчик ввода нового имени
async def process_edit_name(message: types.Message, state: FSMContext):
    new_name = message.text.strip()
    
    if len(new_name) < 2 or len(new_name) > 30:
        await message.answer(MESSAGES["character_creation"]["name_invalid"])
        return
    
    data = await state.get_data()
    character_name = data["character_name"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    # Проверяем, не занято ли новое имя
    if new_name != character_name and character_storage.load_character(message.from_user.id, new_name):
        await message.answer("Персонаж с таким именем уже существует.")
        return
    
    # Обновляем имя персонажа
    character['name'] = new_name
    
    # Сохраняем изменения
    if character_storage.save_character(message.from_user.id, character):
        # Если имя изменилось, удаляем старый файл
        if new_name != character_name:
            character_storage.delete_character(message.from_user.id, character_name)
        await message.answer(f"Имя персонажа успешно изменено на: {new_name}")
    else:
        await message.answer("Произошла ошибка при сохранении изменений.")
    
    await state.clear()

# Обработчик выбора новой расы
async def process_edit_race(message: types.Message, state: FSMContext):
    new_race = message.text.strip()
    
    if new_race not in RACES:
        await message.answer(MESSAGES["common"]["invalid_input"])
        return
    
    data = await state.get_data()
    character_name = data["character_name"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    # Обновляем расу персонажа
    character['race'] = new_race
    
    # Сохраняем изменения
    if character_storage.save_character(message.from_user.id, character):
        await message.answer(f"Раса персонажа успешно изменена на: {new_race}")
    else:
        await message.answer("Произошла ошибка при сохранении изменений.")
    
    await state.clear()

# Обработчик выбора нового класса
async def process_edit_class(message: types.Message, state: FSMContext):
    new_class = message.text.strip()
    
    if new_class not in CLASSES:
        await message.answer(MESSAGES["common"]["invalid_input"])
        return
    
    data = await state.get_data()
    character_name = data["character_name"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    # Обновляем класс персонажа
    character['class_name'] = new_class
    
    # Сохраняем изменения
    if character_storage.save_character(message.from_user.id, character):
        await message.answer(f"Класс персонажа успешно изменен на: {new_class}")
    else:
        await message.answer("Произошла ошибка при сохранении изменений.")
    
    await state.clear()

# Обработчик ввода нового уровня
async def process_edit_level(message: types.Message, state: FSMContext):
    try:
        new_level = int(message.text.strip())
        if new_level < 1 or new_level > 20:
            raise ValueError
    except ValueError:
        await message.answer(MESSAGES["character_creation"]["level_invalid"])
        return
    
    data = await state.get_data()
    character_name = data["character_name"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    # Обновляем уровень персонажа
    character['level'] = new_level
    
    # Сохраняем изменения
    if character_storage.save_character(message.from_user.id, character):
        await message.answer(f"Уровень персонажа успешно изменен на: {new_level}")
    else:
        await message.answer("Произошла ошибка при сохранении изменений.")
    
    await state.clear()

def register_character_management_handlers(dp):
    """Регистрация всех обработчиков управления персонажами"""
    dp.message.register(cmd_list_characters, Command("list_characters"))
    dp.message.register(cmd_view_character, Command("view_character"))
    dp.message.register(cmd_delete_character, Command("delete_character"))
    dp.message.register(cmd_set_proficiencies, Command("set_proficiencies"))
    dp.message.register(cmd_set_expertise, Command("set_expertise"))
    dp.message.register(cmd_set_saving_throws, Command("set_saving_throws"))
    dp.message.register(cmd_set_hit_points, Command("set_hit_points"))
    dp.message.register(cmd_set_armor_class, Command("set_armor_class"))
    dp.message.register(cmd_set_speed, Command("set_speed"))
    dp.message.register(cmd_set_proficiency_bonus, Command("set_proficiency_bonus"))
    dp.message.register(cmd_edit_character, Command("edit_character"))
    
    dp.message.register(process_character_select, CharacterManagement.waiting_for_character_select)
    dp.message.register(process_delete_confirmation, CharacterManagement.waiting_for_delete_confirmation)
    dp.message.register(process_delete_answer, CharacterManagement.waiting_for_delete_answer)
    dp.message.register(process_proficiencies_character, CharacterManagement.waiting_for_proficiencies_character)
    dp.message.register(process_proficiencies_list, CharacterManagement.waiting_for_proficiencies_list)
    dp.message.register(process_expertise_character, CharacterManagement.waiting_for_expertise_character)
    dp.message.register(process_expertise_list, CharacterManagement.waiting_for_expertise_list)
    dp.message.register(process_saving_throws_character, CharacterManagement.waiting_for_saving_throws_character)
    dp.message.register(process_saving_throws_list, CharacterManagement.waiting_for_saving_throws_list)
    dp.message.register(process_hit_points_character, CharacterManagement.waiting_for_hit_points_character)
    dp.message.register(process_hit_points_value, CharacterManagement.waiting_for_hit_points_value)
    dp.message.register(process_armor_class_character, CharacterManagement.waiting_for_armor_class_character)
    dp.message.register(process_armor_class_value, CharacterManagement.waiting_for_armor_class_value)
    dp.message.register(process_speed_character, CharacterManagement.waiting_for_speed_character)
    dp.message.register(process_speed_value, CharacterManagement.waiting_for_speed_value)
    dp.message.register(process_proficiency_bonus_character, CharacterManagement.waiting_for_proficiency_bonus_character)
    dp.message.register(process_proficiency_bonus_value, CharacterManagement.waiting_for_proficiency_bonus_value)
    dp.message.register(process_edit_character, CharacterManagement.waiting_for_edit_character)
    dp.message.register(process_edit_parameter, CharacterManagement.waiting_for_edit_name, F.text.in_(["Имя", "Раса", "Класс", "Уровень"]))
    dp.message.register(process_edit_name, CharacterManagement.waiting_for_edit_name)
    dp.message.register(process_edit_race, CharacterManagement.waiting_for_edit_race)
    dp.message.register(process_edit_class, CharacterManagement.waiting_for_edit_class)
    dp.message.register(process_edit_level, CharacterManagement.waiting_for_edit_level) 