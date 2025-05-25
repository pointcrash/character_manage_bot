import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, BotCommand, BotCommandScopeDefault

from config import BOT_TOKEN, MESSAGES
from handlers.character_creation import register_character_creation_handlers
from handlers.character_management import register_character_management_handlers
from handlers.spell_management import register_spell_management_handlers
from handlers.money_management import register_money_management_handlers
from handlers.inventory_management import register_inventory_management_handlers
from handlers.description_management import register_description_management_handlers
from handlers.active_character import register_active_character_handlers

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Регистрация обработчиков
register_character_creation_handlers(dp)
register_character_management_handlers(dp)
register_spell_management_handlers(dp)
register_money_management_handlers(dp)
register_inventory_management_handlers(dp)
register_description_management_handlers(dp)
register_active_character_handlers(dp)

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(MESSAGES["start"])

# Обработчик команды /help
@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(MESSAGES["help"])

async def set_commands(bot: Bot):
    """Установка меню команд"""
    commands = [
        BotCommand(
            command="help",
            description="Показать справку"
        ),
        BotCommand(
            command="create_character",
            description="Создать нового персонажа"
        ),
        BotCommand(
            command="list_characters",
            description="Показать список персонажей"
        ),
        BotCommand(
            command="view_character",
            description="Просмотреть информацию о персонаже"
        ),
        BotCommand(
            command="edit_character",
            description="Редактировать базовые параметры персонажа"
        ),
        BotCommand(
            command="delete_character",
            description="Удалить персонажа"
        ),
        BotCommand(
            command="set_proficiencies",
            description="Установить владение навыками"
        ),
        BotCommand(
            command="set_expertise",
            description="Установить компетенцию навыков"
        ),
        BotCommand(
            command="set_saving_throws",
            description="Установить владение спасбросками"
        ),
        BotCommand(
            command="set_hit_points",
            description="Установить здоровье"
        ),
        BotCommand(
            command="set_armor_class",
            description="Установить класс брони"
        ),
        BotCommand(
            command="set_speed",
            description="Установить скорость"
        ),
        BotCommand(
            command="set_proficiency_bonus",
            description="Установить бонус мастерства"
        ),
        BotCommand(
            command="set_money",
            description="Управление деньгами персонажа"
        ),
        BotCommand(
            command="inventory",
            description="Управление инвентарем персонажа"
        ),
        BotCommand(
            command="set_description",
            description="Установить описание персонажа"
        ),
        BotCommand(
            command="view_description",
            description="Просмотреть описание персонажа"
        ),
        BotCommand(
            command="view_spells",
            description="Просмотреть магические способности"
        ),
        BotCommand(
            command="set_spell_slots",
            description="Установить ячейки заклинаний"
        ),
        BotCommand(
            command="add_spell",
            description="Добавить заклинание или заговор"
        ),
        BotCommand(
            command="remove_spell",
            description="Удалить заклинание или заговор"
        ),
        BotCommand(
            command="set_active",
            description="Выбрать активного персонажа"
        ),
        BotCommand(
            command="get_active",
            description="Показать текущего активного персонажа"
        )
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

# Запуск бота
async def main():
    # Устанавливаем меню команд
    await set_commands(bot)
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
