"""
Инлайн-клавиатуры и все, что с ними связано
"""
from json import loads
from lxml import html
from lxml.html.clean import clean_html

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def calendar_keyboard(src: str) -> InlineKeyboardMarkup:
    """
    aiogram бета-версии почему-то плохо понимает джейсоны клавиатур
    """
    json_src: dict = loads(src)
    markup: list = json_src.get('inline_keyboard', [])
    result_list: list = []
    for array in markup:
        subarray: list = []
        for item in array:
            subarray.append(InlineKeyboardButton(text=item['text'], callback_data=item['callback_data']))
        result_list.append(subarray)
    return InlineKeyboardMarkup(inline_keyboard=result_list)


def city_keyboard(entities: list) -> InlineKeyboardMarkup:
    result: list = []
    for entity in entities:
        text = str(html.fromstring(entity['caption']).text_content()).strip()
        callback = entity['destinationId']
        result.append([InlineKeyboardButton(text=text, callback_data=callback)])
    return InlineKeyboardMarkup(inline_keyboard=result)


def hotel_keyboard(data: dict, number: int) -> InlineKeyboardMarkup:
    """
    Клавиатура отеля
    """
    btn_map: InlineKeyboardButton = InlineKeyboardButton(text='\U0001F30D Карта',
                                                         callback_data='map#' + str(number))
    btn_url: InlineKeyboardButton = InlineKeyboardButton(text='\U0001F517 Сайт',
                                                         url=data['url'])
    btn_photo: InlineKeyboardButton = InlineKeyboardButton(text='\U0001F4F7 Галерея',
                                                           callback_data='photo#'+str(number))
    return InlineKeyboardMarkup(inline_keyboard=[[btn_map, btn_url, btn_photo]])






