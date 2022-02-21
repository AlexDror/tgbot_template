"""
Главный файл запуска бота
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.dispatcher.fsm.storage.memory import MemoryStorage
from aiogram.dispatcher.fsm.storage.redis import RedisStorage

from tgbot.config import  set_commands, config
from tgbot.handlers.states import register_fsm

logger: logging.Logger = logging.getLogger(__name__)
storage: [RedisStorage, MemoryStorage] = RedisStorage() if config.tg_bot.use_redis \
                                                        else MemoryStorage()
bot:Bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
dp: Dispatcher = Dispatcher(storage=storage)


def register_all_handlers(dp: Dispatcher) -> None:
    """
    Регистрация всех хендлеров
    """
    register_fsm(dp)

async def main():
    """
    Настройка логирования.
    Запуск event-loop и его остановка.
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )
    logger.info("Starting bot")
    await set_commands(bot)
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
