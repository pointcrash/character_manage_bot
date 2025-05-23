from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from config import MESSAGES, CharacterManagement
from storage.character_storage import CharacterStorage

# Инициализация хранилища
character_storage = CharacterStorage()

# Обработчик команды /set_active
async def cmd_set_active(message: types.Message, state: FSMContext):
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
        "Выберите персонажа, которого хотите сделать активным:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_active_character)

# Обработчик выбора активного персонажа
async def process_active_character(message: types.Message, state: FSMContext):
    character_name = message.text.strip()
    character = character_storage.load_character(message.from_user.id, character_name)
    
    if not character:
        await message.answer(
            MESSAGES["common"]["invalid_input"],
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    # Сбрасываем флаг активного персонажа у всех персонажей пользователя
    characters = character_storage.get_user_characters(message.from_user.id)
    for char in characters:
        if char["name"] != character_name:
            char_obj = character_storage.load_character(message.from_user.id, char["name"])
            if char_obj:
                char_obj["is_active"] = False
                character_storage.save_character(message.from_user.id, char_obj)
    
    # Устанавливаем флаг активного персонажа
    character["is_active"] = True
    
    # Сохраняем изменения
    if character_storage.save_character(message.from_user.id, character):
        await message.answer(
            f"Персонаж {character_name} теперь активный!",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "Произошла ошибка при сохранении изменений.",
            reply_markup=ReplyKeyboardRemove()
        )
    
    await state.clear()

# Обработчик команды /get_active
async def cmd_get_active(message: types.Message):
    characters = character_storage.get_user_characters(message.from_user.id)
    
    if not characters:
        await message.answer(MESSAGES["character_management"]["no_characters"])
        return
    
    # Ищем активного персонажа
    active_character = None
    for char in characters:
        if char.get("is_active", False):
            active_character = char
            break
    
    if active_character:
        await message.answer(
            f"Ваш активный персонаж: {active_character['name']} - "
            f"{active_character['race']} {active_character['class_name']} {active_character['level']} уровня"
        )
    else:
        await message.answer(
            "У вас нет активного персонажа. Используйте /set_active чтобы выбрать активного персонажа."
        )

def register_active_character_handlers(dp):
    """Регистрация всех обработчиков управления активным персонажем"""
    dp.message.register(cmd_set_active, Command("set_active"))
    dp.message.register(cmd_get_active, Command("get_active"))
    dp.message.register(process_active_character, CharacterManagement.waiting_for_active_character) 