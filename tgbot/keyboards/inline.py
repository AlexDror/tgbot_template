from json import loads

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def calendar_keyboard(src: str) -> InlineKeyboardMarkup:
    j = loads(src)
    markup = j.get('inline_keyboard', [])
    result_list = []
    for array in markup:
        subarray = []
        for item in array:
            subarray.append(InlineKeyboardButton(text=item['text'], callback_data=item['callback_data']))
        result_list.append(subarray)
    result = InlineKeyboardMarkup(inline_keyboard=result_list)
    return result



