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
    character_data["abilities"] = {
        "strength": abilities[0],
        "dexterity": abilities[1],
        "constitution": abilities[2],
        "intelligence": abilities[3],
        "wisdom": abilities[4],
        "charisma": abilities[5]
    }
    
    # Сохраняем персонажа
    if character_storage.save_character(message.from_user.id, character_data):
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