from aiogram import Router
from aiogram.utils.i18n import I18n, SimpleI18nMiddleware

from tgbot.config import i18n

i18n_middleware = SimpleI18nMiddleware(i18n=i18n)


def register_i18n(dp: Router) -> None:
    """
    Register middleware
    """
    i18n_middleware.setup(router=dp)
