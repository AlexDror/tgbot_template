"""
Главный файл запуска бота
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.dispatcher.fsm.storage.memory import MemoryStorage
from aiogram.dispatcher.fsm.storage.redis import RedisStorage

from tgbot.config import set_commands, config

from tgbot.middlewares.i18n import register_i18n

from tgbot.handlers.admin import register_admin_handlers
from tgbot.handlers.errors import register_error_handler
from tgbot.handlers.users import register_user_handlers


logger: logging.Logger = logging.getLogger(__name__)
storage: [RedisStorage, MemoryStorage] = RedisStorage() if config.tg_bot.use_redis \
                                                        else MemoryStorage()
bot:Bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
dp: Dispatcher = Dispatcher(storage=storage)


def register_all_middlewares(dp: Dispatcher) -> None:
    """
    Регистрация всех миддлварей
    """
    register_i18n(dp)


def register_all_handlers(dp: Dispatcher) -> None:
    """
    Регистрация всех хендлеров
    """
    register_admin_handlers(dp)
    register_user_handlers(dp)
    register_error_handler(dp)

async def main():
    """
    Настройка логирования.
    Запуск event-loop и его остановка.
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )
    logger.info("Starting bot")
    await set_commands(bot)
    register_all_middlewares(dp)
    register_all_handlers(dp)

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
