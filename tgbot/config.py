"""
Конфигурация бота и установка команд
"""
from dataclasses import dataclass

from aiogram import Bot
from aiogram.utils.i18n import I18n
from environs import Env


i18n = I18n(path='locales', default_locale="ru", domain="messages")
_ = i18n.gettext

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
    use_geocode: str = None
    search_exact_matches: str = None


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
            use_geocode=env.str('USE_GEOCODE'),
            search_exact_matches=env.str('SEARCH_EXACT_MATCHES'),
            show_venue = env.str('SHOW_VENUE')

        )
    )

async def set_commands(bot: Bot):
    """
    Установка команд
    """
    pass
    await bot.set_my_commands([{'command':'start', 'description':_('Начало поиска')},
                               {'command': 'help', 'description':_('Помощь')},
                               {'command': 'lowprice', 'description':_('По возрастанию цены')},
                               {'command': 'highprice', 'description':_('По убыванию цены')},
                               {'command': 'bestdeal', 'description':_('Лучший выбор по удаленности и цене')},
                               {'command': 'history', 'description':_('История поиска')},
                               ])

config = load_config('.env')

