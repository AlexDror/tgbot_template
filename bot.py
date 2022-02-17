import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.dispatcher.fsm.storage.memory import MemoryStorage
from aiogram.dispatcher.fsm.storage.redis import RedisStorage

from tgbot.config import load_config, set_commands, config
from tgbot.handlers.admin import register_admin
from tgbot.handlers.echo import register_echo
from tgbot.handlers.states import register_fsm
from tgbot.handlers.user import register_user
from tgbot.middlewares.db import DbMiddleware

logger = logging.getLogger(__name__)
#config = load_config('.env')
storage = RedisStorage() if config.tg_bot.use_redis else MemoryStorage()
bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
dp = Dispatcher(storage=storage)


def register_all_middlewares(dp: Dispatcher):
    dp.update.outer_middleware(DbMiddleware())


def register_all_handlers(dp: Dispatcher):
    register_fsm(dp)
    # register_admin(dp)
    # register_user(dp)
    # register_echo(dp)

async def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )
    logger.info("Starting bot")
    # register_all_middlewares(dp)
    await set_commands(bot)
    register_all_handlers(dp)
    # start
    try:
        await dp.start_polling(bot)
    finally:
        await dp.fsm.storage.close()
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
