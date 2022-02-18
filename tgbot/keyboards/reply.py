from aiogram.types import KeyboardButton

reply_keyboard = [KeyboardButton(text='\U0001F3E0 Старт'),
                  KeyboardButton(text='\U0001F4C6 История')]

btn_config = KeyboardButton(text='\U0001F527 Настройка')

search_keyboard = [[KeyboardButton(text='\U0001F4C8 По возрастанию цены'),
                   KeyboardButton(text='\U0001F4C9 По убыванию цены'),
                   KeyboardButton(text='\U0001F44D Лучший выбор')],
                   [KeyboardButton(text='\U0001F4B5 Диапазон цен')]]