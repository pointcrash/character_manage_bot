from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from config import MESSAGES, CharacterManagement
from storage.character_storage import CharacterStorage

# Инициализация хранилища
character_storage = CharacterStorage()

# Обработчик команды /inventory
async def cmd_inventory(message: types.Message, state: FSMContext):
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
        "Выберите персонажа для управления инвентарем:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_inventory_character)

# Обработчик выбора персонажа для управления инвентарем
async def process_inventory_character(message: types.Message, state: FSMContext):
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
            [KeyboardButton(text="Добавить предмет"), KeyboardButton(text="Удалить предмет")],
            [KeyboardButton(text="Показать инвентарь")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        "Выберите операцию:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_inventory_operation)

# Обработчик выбора операции с инвентарем
async def process_inventory_operation(message: types.Message, state: FSMContext):
    operation = message.text.strip()
    data = await state.get_data()
    character_name = data["character_name"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    if operation == "Показать инвентарь":
        inventory_info = f"🎒 Инвентарь персонажа {character_name}:\n\n"
        
        # Оружие
        inventory_info += "⚔️ Оружие:\n"
        if character['equipment']['weapons']['items']:
            for item in character['equipment']['weapons']['items']:
                inventory_info += f"• {item}\n"
        else:
            inventory_info += "Нет оружия\n"
        
        # Броня
        inventory_info += "\n🛡️ Броня:\n"
        if character['equipment']['armor']['items']:
            for item in character['equipment']['armor']['items']:
                inventory_info += f"• {item}\n"
        else:
            inventory_info += "Нет брони\n"
        
        # Предметы
        inventory_info += "\n📦 Предметы:\n"
        if character['equipment']['items']['items']:
            for item in character['equipment']['items']['items']:
                inventory_info += f"• {item}\n"
        else:
            inventory_info += "Нет предметов\n"
        
        await message.answer(inventory_info, reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return
    
    if operation not in ["Добавить предмет", "Удалить предмет"]:
        await message.answer(
            MESSAGES["common"]["invalid_input"],
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    # Сохраняем операцию в состоянии
    await state.update_data(inventory_operation=operation)
    
    # Создаем клавиатуру с категориями предметов
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Оружие"), KeyboardButton(text="Броня")],
            [KeyboardButton(text="Предметы")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        "Выберите категорию предмета:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_inventory_category)

# Обработчик выбора категории предмета
async def process_inventory_category(message: types.Message, state: FSMContext):
    category = message.text.strip()
    if category not in ["Оружие", "Броня", "Предметы"]:
        await message.answer(
            MESSAGES["common"]["invalid_input"],
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    # Маппинг русских названий на английские ключи
    category_mapping = {
        "Оружие": "weapons",
        "Броня": "armor",
        "Предметы": "items"
    }
    
    # Сохраняем категорию в состоянии
    await state.update_data(inventory_category=category)
    await state.update_data(category_key=category_mapping[category])
    
    data = await state.get_data()
    operation = data["inventory_operation"]
    
    if operation == "Добавить предмет":
        await message.answer(
            "Введите название предмета:",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(CharacterManagement.waiting_for_inventory_item_name)
    else:  # Удалить предмет
        data = await state.get_data()
        character_name = data["character_name"]
        character = character_storage.load_character(message.from_user.id, character_name)
        
        # Получаем список предметов выбранной категории
        category_key = category_mapping[category]
        items = character['equipment'][category_key]['items']
        
        if not items:
            await message.answer(
                f"В категории {category} нет предметов.",
                reply_markup=ReplyKeyboardRemove()
            )
            await state.clear()
            return
        
        # Создаем клавиатуру с предметами для удаления
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=item)] for item in items],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await message.answer(
            "Выберите предмет для удаления:",
            reply_markup=keyboard
        )
        await state.set_state(CharacterManagement.waiting_for_inventory_item_remove)

# Обработчик ввода названия предмета
async def process_inventory_item_name(message: types.Message, state: FSMContext):
    item_name = message.text.strip()
    if not item_name:
        await message.answer("Название предмета не может быть пустым.")
        return
    
    data = await state.get_data()
    character_name = data["character_name"]
    category = data["inventory_category"]
    category_key = data["category_key"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    # Добавляем предмет в соответствующую категорию
    if item_name in character['equipment'][category_key]['items']:
        await message.answer(
            f"Предмет '{item_name}' уже есть в инвентаре.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    character['equipment'][category_key]['items'].append(item_name)
    
    # Сохраняем изменения
    if character_storage.save_character(message.from_user.id, character):
        await message.answer(
            f"Предмет '{item_name}' успешно добавлен в категорию {category}.",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "Произошла ошибка при сохранении изменений.",
            reply_markup=ReplyKeyboardRemove()
        )
    
    await state.clear()

# Обработчик удаления предмета
async def process_inventory_item_remove(message: types.Message, state: FSMContext):
    item_name = message.text.strip()
    data = await state.get_data()
    character_name = data["character_name"]
    category = data["inventory_category"]
    category_key = data["category_key"]
    character = character_storage.load_character(message.from_user.id, character_name)
    
    # Удаляем предмет из соответствующей категории
    if item_name not in character['equipment'][category_key]['items']:
        await message.answer(
            f"Предмет '{item_name}' не найден в категории {category}.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    character['equipment'][category_key]['items'].remove(item_name)
    
    # Сохраняем изменения
    if character_storage.save_character(message.from_user.id, character):
        await message.answer(
            f"Предмет '{item_name}' успешно удален из категории {category}.",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "Произошла ошибка при сохранении изменений.",
            reply_markup=ReplyKeyboardRemove()
        )
    
    await state.clear()

# Обработчик команды /view_equipment
async def cmd_view_equipment(message: types.Message, state: FSMContext):
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
        "Выберите персонажа для просмотра снаряжения:",
        reply_markup=keyboard
    )
    await state.set_state(CharacterManagement.waiting_for_view_equipment_character)

# Обработчик выбора персонажа для просмотра снаряжения
async def process_view_equipment_character(message: types.Message, state: FSMContext):
    character_name = message.text.strip()
    character = character_storage.load_character(message.from_user.id, character_name)
    
    if not character:
        await message.answer(
            MESSAGES["common"]["invalid_input"],
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    # Формируем сообщение с информацией о снаряжении
    equipment_info = f"🎒 Снаряжение персонажа {character_name}:\n\n"
    
    # Оружие
    equipment_info += "⚔️ Оружие:\n"
    if character['equipment']['weapons']['items']:
        for weapon in character['equipment']['weapons']['items']:
            equipment_info += f"• {weapon}\n"
    else:
        equipment_info += "Нет оружия\n"
    
    # Броня
    equipment_info += "\n🛡️ Броня:\n"
    if character['equipment']['armor']['items']:
        for armor in character['equipment']['armor']['items']:
            equipment_info += f"• {armor}\n"
    else:
        equipment_info += "Нет брони\n"
    
    # Предметы
    equipment_info += "\n📦 Предметы:\n"
    if character['equipment']['items']['items']:
        for item in character['equipment']['items']['items']:
            equipment_info += f"• {item}\n"
    else:
        equipment_info += "Нет предметов\n"
    
    # Деньги
    money = character['equipment']['money']
    equipment_info += "\n💰 Деньги:\n"
    if any([money['copper'], money['silver'], money['gold'], money['platinum']]):
        if money['platinum']: equipment_info += f"• {money['platinum']} платиновых\n"
        if money['gold']: equipment_info += f"• {money['gold']} золотых\n"
        if money['silver']: equipment_info += f"• {money['silver']} серебряных\n"
        if money['copper']: equipment_info += f"• {money['copper']} медных\n"
    else:
        equipment_info += "Нет денег\n"
    
    await message.answer(equipment_info, reply_markup=ReplyKeyboardRemove())
    await state.clear()

def register_inventory_management_handlers(dp):
    """Регистрация всех обработчиков управления инвентарем"""
    dp.message.register(cmd_inventory, Command("inventory"))
    dp.message.register(cmd_view_equipment, Command("view_equipment"))
    
    dp.message.register(process_inventory_character, CharacterManagement.waiting_for_inventory_character)
    dp.message.register(process_inventory_operation, CharacterManagement.waiting_for_inventory_operation)
    dp.message.register(process_inventory_category, CharacterManagement.waiting_for_inventory_category)
    dp.message.register(process_inventory_item_name, CharacterManagement.waiting_for_inventory_item_name)
    dp.message.register(process_inventory_item_remove, CharacterManagement.waiting_for_inventory_item_remove)
    dp.message.register(process_view_equipment_character, CharacterManagement.waiting_for_view_equipment_character) 