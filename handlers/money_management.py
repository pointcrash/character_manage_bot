from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from config import MESSAGES, CharacterManagement
from storage.character_storage import CharacterStorage

# Инициализация хранилища
character_storage = CharacterStorage()

# Обработчик команды /set_money
async def cmd_set_money(message: types.Message, state: FSMContext):
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
        "Выберите персонажа для управления деньгами:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_money_character)

# Обработчик выбора персонажа для управления деньгами
async def process_money_character(message: types.Message, state: FSMContext):
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
    
    # Создаем клавиатуру с типами операций
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Добавить"), KeyboardButton(text="Потратить")],
            [KeyboardButton(text="Показать баланс")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        "Выберите операцию:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_money_operation)

# Обработчик выбора операции с деньгами
async def process_money_operation(message: types.Message, state: FSMContext):
    operation = message.text.strip()
    data = await state.get_data()
    character_name = data["character_name"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    if operation == "Показать баланс":
        money = character['equipment']['money']
        balance_info = f"💰 Баланс персонажа {character_name}:\n"
        
        # Проверяем, все ли значения равны нулю
        all_zero = all(value == 0 for value in money.values())
        
        if all_zero:
            balance_info += f"• {money['platinum']} платиновых\n"
            balance_info += f"• {money['gold']} золотых\n"
            balance_info += f"• {money['silver']} серебряных\n"
            balance_info += f"• {money['copper']} медных"
        else:
            # Добавляем только ненулевые значения
            if money['platinum'] > 0:
                balance_info += f"• {money['platinum']} платиновых\n"
            if money['gold'] > 0:
                balance_info += f"• {money['gold']} золотых\n"
            if money['silver'] > 0:
                balance_info += f"• {money['silver']} серебряных\n"
            if money['copper'] > 0:
                balance_info += f"• {money['copper']} медных"
        
        await message.answer(balance_info, reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return
    
    if operation not in ["Добавить", "Потратить"]:
        await message.answer(
            MESSAGES["common"]["invalid_input"],
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    # Сохраняем операцию в состоянии
    await state.update_data(money_operation=operation)
    
    await message.answer(
        f"Введите количество монет через пробел в следующем порядке:\n"
        f"платиновые золотые серебряные медные\n"
        f"Например: '0 10 5 0'\n\n"
        f"Текущий баланс:\n"
        f"• {character['equipment']['money']['platinum']} платиновых\n"
        f"• {character['equipment']['money']['gold']} золотых\n"
        f"• {character['equipment']['money']['silver']} серебряных\n"
        f"• {character['equipment']['money']['copper']} медных",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CharacterManagement.waiting_for_money_amount)

# Обработчик ввода количества денег
async def process_money_amount(message: types.Message, state: FSMContext):
    try:
        # Разбиваем ввод на значения монет
        values = message.text.strip().split()
        if len(values) != 4:
            await message.answer("Пожалуйста, введите 4 значения через пробел (платиновые золотые серебряные медные)")
            return
            
        coins = [int(value) for value in values]
        if any(coin < 0 for coin in coins):
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите положительные числа.")
        return
    
    data = await state.get_data()
    character_name = data["character_name"]
    operation = data["money_operation"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    # Обновляем значения денег
    if operation == "Добавить":
        character['equipment']['money']['platinum'] += coins[0]
        character['equipment']['money']['gold'] += coins[1]
        character['equipment']['money']['silver'] += coins[2]
        character['equipment']['money']['copper'] += coins[3]
    else:  # Потратить
        # Проверяем, достаточно ли денег
        if (character['equipment']['money']['platinum'] < coins[0] or
            character['equipment']['money']['gold'] < coins[1] or
            character['equipment']['money']['silver'] < coins[2] or
            character['equipment']['money']['copper'] < coins[3]):
            await message.answer("Недостаточно денег для совершения операции.")
            await state.clear()
            return
        
        character['equipment']['money']['platinum'] -= coins[0]
        character['equipment']['money']['gold'] -= coins[1]
        character['equipment']['money']['silver'] -= coins[2]
        character['equipment']['money']['copper'] -= coins[3]
    
    # Сохраняем изменения
    if character_storage.save_character(message.from_user.id, character):
        money = character['equipment']['money']
        balance_info = "Баланс успешно обновлен:\n"
        
        # Проверяем, все ли значения равны нулю
        all_zero = all(value == 0 for value in money.values())
        
        if all_zero:
            balance_info += f"• {money['platinum']} платиновых\n"
            balance_info += f"• {money['gold']} золотых\n"
            balance_info += f"• {money['silver']} серебряных\n"
            balance_info += f"• {money['copper']} медных"
        else:
            # Добавляем только ненулевые значения
            if money['platinum'] > 0:
                balance_info += f"• {money['platinum']} платиновых\n"
            if money['gold'] > 0:
                balance_info += f"• {money['gold']} золотых\n"
            if money['silver'] > 0:
                balance_info += f"• {money['silver']} серебряных\n"
            if money['copper'] > 0:
                balance_info += f"• {money['copper']} медных"
        
        await message.answer(balance_info)
    else:
        await message.answer("Произошла ошибка при сохранении изменений.")
    
    await state.clear()

def register_money_management_handlers(dp):
    """Регистрация всех обработчиков управления деньгами"""
    dp.message.register(cmd_set_money, Command("set_money"))
    
    dp.message.register(process_money_character, CharacterManagement.waiting_for_money_character)
    dp.message.register(process_money_operation, CharacterManagement.waiting_for_money_operation)
    dp.message.register(process_money_amount, CharacterManagement.waiting_for_money_amount) 