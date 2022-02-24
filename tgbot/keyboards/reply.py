"""
Reply-клавиатуры и все, что с ними связано
"""
from aiogram.types import KeyboardButton
#from aiogram.utils.i18n import gettext as _
from tgbot.config import i18n

_ = i18n.gettext

reply_keyboard: list = [KeyboardButton(text='\U0001F3E0 ' + _('Старт')),
                        KeyboardButton(text='\U0001F4C6 ' + _('История'))]

btn_config: KeyboardButton = KeyboardButton(text='\U0001F527 ' + _('Настройка'))

search_keyboard: list = [[KeyboardButton(text='\U0001F4C8 ' + _('По возрастанию цены')),
                   KeyboardButton(text='\U0001F4C9 ' + _('По убыванию цены')),
                   KeyboardButton(text='\U0001F44D ' + _('Лучший выбор'))],
                   [KeyboardButton(text='\U0001F4B5 ' + _('Диапазон цен'))]]

btn_show_more: KeyboardButton = KeyboardButton(text='\U000023E9 ' + _('Показать еще...'))