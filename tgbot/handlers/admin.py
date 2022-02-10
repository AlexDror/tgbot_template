from aiogram import Dispatcher, F
from aiogram.dispatcher.filters import Command
from aiogram.types import Message

from tgbot.config import load_config

admins = load_config('.env').tg_bot.admin_ids

async def admin_start(message: Message):
    await message.reply("Hello, admin!")

def register_admin(dp: Dispatcher):
    dp.message.register(admin_start, Command(commands=["start"]), F.from_user.id.in_(admins))
