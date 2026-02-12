import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command

from bot.config import settings
from bot.db import init_db
from bot.handlers import commands, narrator, partner, npc
from bot.router import route_message
from aiogram.types import Message
from aiogram import F

logger = logging.getLogger(__name__)

dp = Dispatcher()

@dp.message(Command(commands=['start', 'help', 'notes', 'evidence']))
async def cmd_handler(message: Message):
    await commands.handle(message)

@dp.message(F.text)
async def text_handler(message: Message):
    user_id = message.from_user.id
    text = message.text
    response = await route_message(text, user_id)
    await message.answer(response, parse_mode=ParseMode.HTML)

async def main():
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    await init_db()
    bot = Bot(
        token=settings.TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
