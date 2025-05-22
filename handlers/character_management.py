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
    
    # Удваиваем бонус мастерства если навык в списке экспертизы
    if skill in character['advanced_stats']['skills']['expertise']:
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
    
    # Добавляем информацию о навыках
    character_info += f"\nНавыки:\n"
    proficiencies = character['advanced_stats']['skills']['proficiencies']
    expertise = character['advanced_stats']['skills']['expertise']
    
    for skill, _ in character['advanced_stats']['skills']['values'].items():
        value = calculate_skill_value(character, skill)
        if skill in expertise:
            character_info += f"⭐ {skill}: {value:+d} (Эксперт)\n"
        elif skill in proficiencies:
            character_info += f"✓ {skill}: {value:+d} (Мастерство)\n"
        else:
            character_info += f"  {skill}: {value:+d}\n"
    
    # Добавляем информацию о снаряжении
    character_info += f"\nСнаряжение:\n"
    
    # Оружие
    if character['equipment']['weapons']['items']:
        character_info += f"Оружие:\n"
        for weapon in character['equipment']['weapons']['items']:
            character_info += f"  • {weapon}\n"
    
    # Броня
    if character['equipment']['armor']['items']:
        character_info += f"Броня:\n"
        for armor in character['equipment']['armor']['items']:
            character_info += f"  • {armor}\n"
    
    # Предметы
    if character['equipment']['items']['items']:
        character_info += f"Предметы:\n"
        for item in character['equipment']['items']['items']:
            character_info += f"  • {item}\n"
    
    # Деньги
    money = character['equipment']['money']
    if any([money['copper'], money['silver'], money['gold'], money['platinum']]):
        character_info += f"Деньги:\n"
        if money['platinum']: character_info += f"  • {money['platinum']} платиновых\n"
        if money['gold']: character_info += f"  • {money['gold']} золотых\n"
        if money['silver']: character_info += f"  • {money['silver']} серебряных\n"
        if money['copper']: character_info += f"  • {money['copper']} медных\n"
    
    # Добавляем информацию о магических способностях
    if any(character['magic']['spell_slots']['values'].values()):
        character_info += f"\nМагические способности:\n"
        
        # Ячейки заклинаний
        spell_slots = character['magic']['spell_slots']['values']
        if any(spell_slots.values()):
            character_info += f"Ячейки заклинаний:\n"
            for level, slots in spell_slots.items():
                if slots > 0:
                    character_info += f"  • {level} уровень: {slots}\n"
        
        # Известные заклинания
        if character['magic']['spells_known']['cantrips'] or character['magic']['spells_known']['spells']:
            character_info += f"Известные заклинания:\n"
            if character['magic']['spells_known']['cantrips']:
                character_info += f"  Заговоры:\n"
                for spell in character['magic']['spells_known']['cantrips']:
                    character_info += f"    • {spell}\n"
            if character['magic']['spells_known']['spells']:
                character_info += f"  Заклинания:\n"
                for spell in character['magic']['spells_known']['spells']:
                    character_info += f"    • {spell}\n"
        
        # Параметры заклинаний
        if character['magic']['spell_save_dc']['value'] or character['magic']['spell_attack_bonus']['value']:
            character_info += f"Параметры заклинаний:\n"
            if character['magic']['spell_save_dc']['value']:
                character_info += f"  • Сложность спасброска: {character['magic']['spell_save_dc']['value']}\n"
            if character['magic']['spell_attack_bonus']['value']:
                character_info += f"  • Бонус к атаке: +{character['magic']['spell_attack_bonus']['value']}\n"
    
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