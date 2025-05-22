from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from config import MESSAGES, CharacterManagement
from storage.character_storage import CharacterStorage

# Инициализация хранилища
character_storage = CharacterStorage()

def calculate_modifier(ability_score: int) -> int:
    """Рассчитать модификатор характеристики"""
    return (ability_score - 10) // 2

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

def register_character_management_handlers(dp):
    """Регистрация всех обработчиков управления персонажами"""
    dp.message.register(cmd_list_characters, Command("list_characters"))
    dp.message.register(cmd_view_character, Command("view_character"))
    dp.message.register(cmd_delete_character, Command("delete_character"))
    
    dp.message.register(process_character_select, CharacterManagement.waiting_for_character_select)
    dp.message.register(process_delete_confirmation, CharacterManagement.waiting_for_delete_confirmation)
    dp.message.register(process_delete_answer, CharacterManagement.waiting_for_delete_answer) 