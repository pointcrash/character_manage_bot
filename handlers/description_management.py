from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from config import MESSAGES, CharacterManagement
from storage.character_storage import CharacterStorage

# Инициализация хранилища
character_storage = CharacterStorage()

# Обработчик команды /set_description
async def cmd_set_description(message: types.Message, state: FSMContext):
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
        "Выберите персонажа для установки описания:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_description_character)

# Обработчик выбора персонажа для установки описания
async def process_description_character(message: types.Message, state: FSMContext):
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
    
    # Показываем текущее описание, если оно есть
    current_description = character.get('description', '')
    if current_description:
        await message.answer(
            f"Текущее описание персонажа:\n\n{current_description}\n\n"
            "Введите новое описание персонажа:",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "Введите описание персонажа:",
            reply_markup=ReplyKeyboardRemove()
        )
    
    await state.set_state(CharacterManagement.waiting_for_description_text)

# Обработчик ввода описания персонажа
async def process_description_text(message: types.Message, state: FSMContext):
    description = message.text.strip()
    if not description:
        await message.answer("Описание не может быть пустым.")
        return
    
    data = await state.get_data()
    character_name = data["character_name"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    # Обновляем описание персонажа
    character['description'] = description
    
    # Сохраняем изменения
    if character_storage.save_character(message.from_user.id, character):
        await message.answer(
            f"Описание персонажа {character_name} успешно обновлено.",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "Произошла ошибка при сохранении изменений.",
            reply_markup=ReplyKeyboardRemove()
        )
    
    await state.clear()

# Обработчик команды /view_description
async def cmd_view_description(message: types.Message, state: FSMContext):
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
        "Выберите персонажа для просмотра описания:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_view_description_character)

# Обработчик выбора персонажа для просмотра описания
async def process_view_description_character(message: types.Message, state: FSMContext):
    character_name = message.text.strip()
    character = character_storage.load_character(message.from_user.id, character_name)
    
    if not character:
        await message.answer(
            MESSAGES["common"]["invalid_input"],
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    description = character.get('description', '')
    if description:
        await message.answer(
            f"📝 Описание персонажа {character_name}:\n\n{description}",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            f"У персонажа {character_name} пока нет описания. Используйте /set_description чтобы добавить описание.",
            reply_markup=ReplyKeyboardRemove()
        )
    
    await state.clear()

def register_description_management_handlers(dp):
    """Регистрация всех обработчиков управления описанием"""
    dp.message.register(cmd_set_description, Command("set_description"))
    dp.message.register(cmd_view_description, Command("view_description"))
    
    dp.message.register(process_description_character, CharacterManagement.waiting_for_description_character)
    dp.message.register(process_description_text, CharacterManagement.waiting_for_description_text)
    dp.message.register(process_view_description_character, CharacterManagement.waiting_for_view_description_character) 