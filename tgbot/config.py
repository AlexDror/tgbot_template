"""
Конфигурация бота и установка команд
"""
from dataclasses import dataclass

from aiogram import Bot
from environs import Env

@dataclass
class DbConfig:
    """
    Конфигурация соединения с БД
    """
    host: str
    port: str
    password: str
    user: str
    database: str

@dataclass
class TgBot:
    """
    Конфигурация бота
    """
    token: str
    admin_ids: list[int]
    use_redis: bool
    api_token: str

@dataclass
class Miscellaneous:
    """
    Дополнительные параметры конфигурации
    """
    max_hotels: str = None
    currency: str = None
    currency_sym: str = None
    app_name: str = None
    show_thumbnails: str = None
    hotels_per_page: str = None
    pictures_per_page: str = None
    show_venue: str = None


@dataclass
class Config:
    """
    Все вместе
    """
    tg_bot: TgBot
    db: DbConfig
    misc: Miscellaneous


def load_config(path: str = None):
    """
    Загрузка данных из конфигурационного файла
    """
    env: Env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"),
            admin_ids=list(map(int, env.list("ADMINS"))),
            use_redis=env.bool("USE_REDIS"),
            api_token=env.str('APITOKEN')
        ),
        db=DbConfig(
            host=env.str('DB_HOST'),
            port=env.str('DB_PORT'),
            password=env.str('DB_PASS'),
            user=env.str('DB_USER'),
            database=env.str('DB_NAME')
        ),
        misc=Miscellaneous(
            max_hotels=env.str('MAX_HOTELS'),
            currency=env.str('CURRENCY'),
            currency_sym=env.str('CURRENCY_SYM'),
            show_thumbnails=env.str('SHOW_THUMBNAILS'),
            hotels_per_page=env.str('HOTELS_PER_PAGE'),
            app_name=env.str('APP_NAME'),
            pictures_per_page = env.str('PICTURES_PER_PAGE'),
            show_venue = env.str('SHOW_VENUE')

        )
    )

async def set_commands(bot: Bot):
    """
    Установка команд
    """
    await bot.set_my_commands([{'command':'start', 'description':'Начало поиска'},
                               {'command': 'help', 'description':'Помощь'},
                               {'command': 'lowprice', 'description':'По возрастанию цены'},
                               {'command': 'highprice', 'description':'По убыванию цены'},
                               {'command': 'bestdeal', 'description':'Лучший выбор по удаленности и цене'},
                               {'command': 'history', 'description':'История поиска'},
                               ])

config = load_config('.env')

