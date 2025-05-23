import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

from config import BOT_TOKEN, MESSAGES
from handlers.character_creation import register_character_creation_handlers
from handlers.character_management import register_character_management_handlers
from handlers.spell_management import register_spell_management_handlers
from handlers.money_management import register_money_management_handlers

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

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(MESSAGES["start"])

# Обработчик команды /help
@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(MESSAGES["help"])

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
