import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from config import (
    BOT_TOKEN, MESSAGES, CharacterCreation,
    RACES, CLASSES
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(MESSAGES["start"])

# Обработчик команды /help
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(MESSAGES["help"])

# Обработчик команды /create_character
@dp.message(Command("create_character"))
async def cmd_create_character(message: types.Message, state: FSMContext):
    await message.answer(MESSAGES["character_creation"]["start"])
    await state.set_state(CharacterCreation.waiting_for_name)

# Обработчик ввода имени
@dp.message(CharacterCreation.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if not 2 <= len(name) <= 30:
        await message.answer(MESSAGES["character_creation"]["name_invalid"])
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
@dp.message(CharacterCreation.waiting_for_race)
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
@dp.message(CharacterCreation.waiting_for_class)
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
@dp.message(CharacterCreation.waiting_for_level)
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
@dp.message(CharacterCreation.waiting_for_abilities)
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
    
    # TODO: Сохранить данные персонажа в базу данных
    
    await message.answer(MESSAGES["character_creation"]["success"])
    await state.clear()

# Функция запуска бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
