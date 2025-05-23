import re
from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from config import MESSAGES, CharacterManagement
from storage.character_storage import CharacterStorage

# Инициализация хранилища
character_storage = CharacterStorage()

# Обработчик команды /set_spell_slots
async def cmd_set_spell_slots(message: types.Message, state: FSMContext):
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
        "Выберите персонажа для установки ячеек заклинаний:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_spell_slots_character)

# Обработчик выбора персонажа для установки ячеек заклинаний
async def process_spell_slots_character(message: types.Message, state: FSMContext):
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
    
    # Показываем текущие значения ячеек заклинаний
    current_slots = character['magic']['spell_slots']['values']
    slots_info = "\n".join(f"Уровень {level}: {slots}" for level, slots in current_slots.items() if slots > 0)
    
    await message.answer(
        f"Введите количество ячеек заклинаний для каждого уровня через пробел (например: '4 3 2 1')\n"
        f"Текущие значения:\n{slots_info}",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CharacterManagement.waiting_for_spell_slots_values)

# Обработчик ввода значений ячеек заклинаний
async def process_spell_slots_values(message: types.Message, state: FSMContext):
    try:
        # Разбиваем ввод на значения для каждого уровня
        values = [int(value) for value in message.text.strip().split()]
        if len(values) > 9:  # Максимум 9 уровней заклинаний
            await message.answer("Максимальный уровень заклинаний - 9.")
            return
            
        if any(value < 0 for value in values):
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите положительные числа.")
        return
    
    data = await state.get_data()
    character_name = data["character_name"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    # Обновляем значения ячеек заклинаний
    for level, slots in enumerate(values, 1):
        character['magic']['spell_slots']['values'][str(level)] = slots
    
    # Сохраняем изменения
    if character_storage.save_character(message.from_user.id, character):
        slots_info = "\n".join(f"Уровень {level}: {slots}" for level, slots in enumerate(values, 1) if slots > 0)
        await message.answer(f"Ячейки заклинаний успешно обновлены:\n{slots_info}")
    else:
        await message.answer("Произошла ошибка при сохранении изменений.")
    
    await state.clear()

# Обработчик команды /add_spell
async def cmd_add_spell(message: types.Message, state: FSMContext):
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
        "Выберите персонажа для добавления заклинания:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_add_spell_character)

# Обработчик выбора персонажа для добавления заклинания
async def process_add_spell_character(message: types.Message, state: FSMContext):
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
    
    # Создаем клавиатуру с типами заклинаний
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Заговор"), KeyboardButton(text="Заклинание")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        "Выберите тип заклинания:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_spell_type)

# Обработчик выбора типа заклинания
async def process_spell_type(message: types.Message, state: FSMContext):
    spell_type = message.text.strip()
    
    if spell_type not in ["Заговор", "Заклинание"]:
        await message.answer(
            MESSAGES["common"]["invalid_input"],
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    # Сохраняем тип заклинания в состоянии
    await state.update_data(spell_type=spell_type)
    
    if spell_type == "Заклинание":
        # Создаем клавиатуру с уровнями заклинаний
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=str(i))] for i in range(1, 10)],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(
            "Выберите уровень заклинания:",
            reply_markup=keyboard
        )
        await state.set_state(CharacterManagement.waiting_for_spell_level)
    else:
        await message.answer(
            "Введите название заговора:",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(CharacterManagement.waiting_for_spell_name)

# Обработчик выбора уровня заклинания
async def process_spell_level(message: types.Message, state: FSMContext):
    try:
        level = int(message.text.strip())
        if level < 1 or level > 9:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, выберите уровень от 1 до 9.")
        return
    
    # Сохраняем уровень заклинания в состоянии
    await state.update_data(spell_level=level)
    
    await message.answer(
        "Введите название заклинания:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CharacterManagement.waiting_for_spell_name)

# Обработчик ввода названия заклинания
async def process_spell_name(message: types.Message, state: FSMContext):
    spell_name = message.text.strip()
    data = await state.get_data()
    character_name = data["character_name"]
    spell_type = data["spell_type"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    if spell_type == "Заговор":
        # Добавляем заговор
        if spell_name not in character['magic']['spells_known']['cantrips']:
            character['magic']['spells_known']['cantrips'].append(spell_name)
    else:
        # Добавляем заклинание
        spell_level = data["spell_level"]
        spell_name_with_level = f"{spell_name} ({spell_level} уровень)"
        if spell_name_with_level not in character['magic']['spells_known']['spells']:
            character['magic']['spells_known']['spells'].append(spell_name_with_level)

            def extract_level(spell):
                match = re.search(r"\((\d+) уровень\)", spell)
                return int(match.group(1)) if match else 0

            # Сортируем список по уровню
            character['magic']['spells_known']['spells'] = sorted(
                character['magic']['spells_known']['spells'], key=extract_level)
    
    # Сохраняем изменения
    if character_storage.save_character(message.from_user.id, character):
        if spell_type == "Заговор":
            await message.answer(f"Заговор '{spell_name}' успешно добавлен.")
        else:
            await message.answer(f"Заклинание '{spell_name_with_level}' успешно добавлено.")
    else:
        await message.answer("Произошла ошибка при сохранении изменений.")
    
    await state.clear()

# Обработчик команды /remove_spell
async def cmd_remove_spell(message: types.Message, state: FSMContext):
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
        "Выберите персонажа для удаления заклинания:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_remove_spell_character)

# Обработчик выбора персонажа для удаления заклинания
async def process_remove_spell_character(message: types.Message, state: FSMContext):
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
    
    # Создаем клавиатуру с типами заклинаний
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Заговор"), KeyboardButton(text="Заклинание")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        "Выберите тип заклинания для удаления:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_remove_spell_type)

# Обработчик выбора типа заклинания для удаления
async def process_remove_spell_type(message: types.Message, state: FSMContext):
    spell_type = message.text.strip()
    data = await state.get_data()
    character_name = data["character_name"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    if spell_type not in ["Заговор", "Заклинание"]:
        await message.answer(
            MESSAGES["common"]["invalid_input"],
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    # Создаем клавиатуру со списком заклинаний
    spells = character['magic']['spells_known']['cantrips'] if spell_type == "Заговор" else character['magic']['spells_known']['spells']
    
    if not spells:
        await message.answer(f"У персонажа нет {spell_type.lower()}ов.")
        await state.clear()
        return
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=spell)] for spell in spells],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        f"Выберите {spell_type.lower()} для удаления:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_remove_spell_name)

# Обработчик выбора заклинания для удаления
async def process_remove_spell_name(message: types.Message, state: FSMContext):
    spell_name = message.text.strip()
    data = await state.get_data()
    character_name = data["character_name"]
    spell_type = data["spell_type"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    if spell_type == "Заговор":
        if spell_name in character['magic']['spells_known']['cantrips']:
            character['magic']['spells_known']['cantrips'].remove(spell_name)
    else:
        if spell_name in character['magic']['spells_known']['spells']:
            character['magic']['spells_known']['spells'].remove(spell_name)
    
    # Сохраняем изменения
    if character_storage.save_character(message.from_user.id, character):
        await message.answer(f"{spell_type} '{spell_name}' успешно удален.")
    else:
        await message.answer("Произошла ошибка при сохранении изменений.")
    
    await state.clear()

def register_spell_management_handlers(dp):
    """Регистрация всех обработчиков управления заклинаниями"""
    dp.message.register(cmd_set_spell_slots, Command("set_spell_slots"))
    dp.message.register(cmd_add_spell, Command("add_spell"))
    dp.message.register(cmd_remove_spell, Command("remove_spell"))
    
    dp.message.register(process_spell_slots_character, CharacterManagement.waiting_for_spell_slots_character)
    dp.message.register(process_spell_slots_values, CharacterManagement.waiting_for_spell_slots_values)
    dp.message.register(process_add_spell_character, CharacterManagement.waiting_for_add_spell_character)
    dp.message.register(process_spell_type, CharacterManagement.waiting_for_spell_type)
    dp.message.register(process_spell_level, CharacterManagement.waiting_for_spell_level)
    dp.message.register(process_spell_name, CharacterManagement.waiting_for_spell_name)
    dp.message.register(process_remove_spell_character, CharacterManagement.waiting_for_remove_spell_character)
    dp.message.register(process_remove_spell_type, CharacterManagement.waiting_for_remove_spell_type)
    dp.message.register(process_remove_spell_name, CharacterManagement.waiting_for_remove_spell_name) 