from dataclasses import dataclass

from aiogram import Bot
from aiogram.types import BotCommand
from environs import Env

@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str

@dataclass
class TgBot:
    token: str
    admin_ids: list[int]
    use_redis: bool
    api_token: str

@dataclass
class Miscellaneous:
    other_params: str = None
    max_hotels: str = None


@dataclass
class Config:
    tg_bot: TgBot
    db: DbConfig
    misc: Miscellaneous


def load_config(path: str = None):
    env = Env()
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
            password=env.str('DB_PASS'),
            user=env.str('DB_USER'),
            database=env.str('DB_NAME')
        ),
        misc=Miscellaneous(
            max_hotels=env.str(MAX_HOTELS)
        )
    )

async def set_commands(bot: Bot):
    await bot.set_my_commands([{'command':'start', 'description':'Начало поиска'},
                               {'command': 'help', 'description':'Помощь'},
                               {'command': 'lowprice', 'description':'По возрастанию цены'},
                               {'command': 'highprice', 'description':'По убыванию цены'},
                               {'command': 'bestdeal', 'description':'Лучший выбор по удаленности и цене'},
                               {'command': 'history', 'description':'История поиска'},
                               ])

config = load_config('.env')

