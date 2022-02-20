import datetime
import json
import logging

from geopy import Nominatim
from geopy.adapters import AioHTTPAdapter
from jinja2 import Template
from math import ceil, pi, sin, cos, atan2, sqrt, pow, atan, asin
from typing import Dict, Any

from aiogram import Router, F, html
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineQuery, \
    InlineKeyboardMarkup, CallbackQuery, InlineKeyboardButton
from aiohttp.client import ClientSession
from telegram_bot_calendar import DetailedTelegramCalendar

from tgbot.keyboards.inline import calendar_keyboard
from tgbot.keyboards.reply import reply_keyboard, btn_config, search_keyboard
from tgbot.misc.aiogoogletrans2.client import Translator
from tgbot.misc.api_locales import hotels_api_locales
from tgbot.misc.templates import hotel_card
from tgbot.models.fsm import Form, HotelBotForm
from tgbot.config import config

ADMINS = config.tg_bot.admin_ids
APIKEY = config.tg_bot.api_token
sticker_id = 'CAACAgIAAxkBAAIFaWIQoWdm_f-gOqa-T-wXBsjD5LRmAAJQCwACLw_wBqRaqc_7Le0YIwQ'


async def command_start(message: Message, state: FSMContext) -> None:
    """
    Хендлер начала работы.
    Сбрасываем состояние, приветствуем пользователя и ожидаем ввода названия города.
    Сохраняем пользовательскую локаль и id чата
    :param message:
    :param state:
    :return:
    """
    await state.clear()
    await state.set_state(HotelBotForm.init)
    await state.update_data(locale=message.from_user.language_code)
    await state.update_data(chat_id=message.chat.id)
    main_keyboard = reply_keyboard[:]
    if message.from_user.id in ADMINS:
        main_keyboard.append(btn_config)
    await message.delete()
    await state.update_data(main_keyboard=main_keyboard)
    await message.answer('Вас приветствует телеграм-бот туристического агентства TooEasyTravel!\n'
                         'Я попробую найти для Вас комфортный отель по заданным Вами условиям,'
                         'и я уверен, у нас все получится! Если Вы готовы, введите название '
                         'города, в котором Вы планируете остановиться',
                         reply_markup=ReplyKeyboardMarkup(keyboard=[main_keyboard],
                                                          resize_keyboard=True,),)


async def command_history(message: Message, state: FSMContext) -> None:
    """
    Хендлер показа истории запросов
    """
    await message.answer('Здесь будет история поисков')
    await message.delete()


async def command_config(message: Message, state: FSMContext) -> None:
    """
    Хендлер админского меню конфигурирования параметров бота
    :param message:
    :param state:
    :return:
    """
    await message.delete()
    config_messages = []
    config_messages.append(await message.answer('Здесь можно настроить дополнительные параметры бота'))
    config_messages.append(await message.answer('Доступны следующие параметры:'))
    variables = config.misc.__dict__.keys()
    for var in variables:
        config_messages.append(await message.answer(var + ' = ' + getattr(config.misc, var)))
    config_messages.append(await message.answer('Введите имя параметра и его новое значение зерез символ "=" без пробелов, окончание ввода - 0'))
    current_state = await state.get_state()
    await state.update_data(previous_state=current_state, config_messages=config_messages)
    await state.set_state(HotelBotForm.config)

async def command_setprices(message:Message, state:FSMContext) -> None:
    """
    Хендлер команды установки границ цен отелей
    :param message:
    :param state:
    :return:
    """
    config_messages = [await message.delete()]
    await state.set_state(HotelBotForm.set_price1)
    config_messages.append(await message.answer('Введите минимальную цену: '))
    state.update_data(config_messages=config_messages)

async def command_show(message: Message, state: FSMContext):
    data = await state.get_data()
    thumb, caption = message_hotel(data, 0)
    await message.answer_photo(thumb, caption, parse_mode='HTML')
    thumb, caption = message_hotel(data, 1)
    await message.answer_photo(thumb, caption, parse_mode='HTML')
    thumb, caption = message_hotel(data, 2)
    await message.answer_photo(thumb, caption, parse_mode='HTML')
    thumb, caption = message_hotel(data, 3)
    await message.answer_photo(thumb, caption, parse_mode='HTML')


async def process_config(message: Message, state: FSMContext):
    data = await state.get_data()
    config_messages = data['config_messages']
    config_messages.append(message)
    if message.text=='0':
        await state.set_state(data['previous_state'])
        for mes in config_messages:
            await mes.delete()
        await state.update_data(config_messages=[])
    else:
        try:
            config_messages.append(message)
            values = message.text.split('=')
            setattr(config.misc, values[0], values[1])
            config_messages.append(await message.answer('Ok'))
        except Exception(exept):
            config_messages.append(await message.answer(exept))


async def process_city(message: Message, state: FSMContext):
    watches = await message.answer_sticker(sticker_id)
    # city_text = message.text
    # translator = Translator()
    # tr_city_text = await translator.translate(text=city_text)
    # if tr_city_text.src == 'bg' and message.from_user.language_code == 'ru':
    #     translator = Translator()
    #     tr_city_text = await translator.translate(text=city_text, src='ru')
    # city_text = tr_city_text.text
    # url = "https://hotels4.p.rapidapi.com/locations/v2/search"
    # querystring = {"query": city_text, "locale": 'en_US', "currency": "USD"}
    # headers = {
    #             'x-rapidapi-host': "hotels4.p.rapidapi.com",
    #             'x-rapidapi-key': APIKEY
    #           }
    # async with ClientSession() as session:
    #     async with session.get(url, headers=headers, params=querystring) as resp:
    #         if resp.status == 200:
    #             resp_text = await resp.text()
    #             resp_json = json.loads(resp_text)
    #             try:
    #                 city_id = resp_json['suggestions'][0]['entities'][0]['destinationId']
    #                 latitude = resp_json['suggestions'][0]['entities'][0]['latitude']
    #                 longitude = resp_json['suggestions'][0]['entities'][0]['latitude']
    #             except IndexError:
    #                 city_not_found = True
    city_not_found = False
    city_text = 'Moscow'
    city_id = '1153093'
    async with Nominatim(user_agent=config.misc.app_name, adapter_factory=AioHTTPAdapter, ) as geolocator:
        location = await geolocator.geocode({'city': city_text})
    latitude = location.latitude
    longitude = location.longitude

    if city_not_found:
        await message.reply('К сожалению, не могу найти такого города, попробуйте еще раз...')
    else:
        await message.reply(city_id)
        await message.reply(city_text)
        await state.update_data(city_text=city_text)
        await state.update_data(city_id=city_id)
        await state.update_data(city_lat=latitude)
        await state.update_data(city_lon=longitude)
        await state.set_state(HotelBotForm.date_from)
        calendar_locale = 'ru' if message.from_user.language_code == 'ru' else 'en'
        min_date = datetime.date.today()
        calendar, step = DetailedTelegramCalendar(locale=calendar_locale, min_date=min_date).build()
        await message.answer(text='Выберите дату заезда', reply_markup=calendar_keyboard(calendar))
    await watches.delete()




async def process_calendar(query: [CallbackQuery, Message], state: FSMContext):
    first = await state.get_state() == 'HotelBotForm:date_from'
    data = await state.get_data()
    if isinstance(query, Message):
        if first:
            try:
                date_from = datetime.datetime.strptime(query.text, '%Y-%m-%d')
                if date_from < datetime.datetime.today():
                    raise ValueError
                await state.update_data(date_from=date_from)
                await state.set_state(HotelBotForm.date_to)
            except ValueError:
                await query.answer('Неверная дата, попробуйте еще раз')
        else:
            try:
                date_to = datetime.datetime.strptime(query.text, '%Y-%m-%d')
                date_from = data['date_from']
                if date_to < date_from:
                    raise ValueError
                await state.update_data(date_to=date_to)
                nights = max((date_to - date_from).days(), 1)
                await state.update_data(nights=nights)
                await state.set_state(HotelBotForm.sort_order)
                main_keyboard = data['main_keyboard']
                new_keyboard = search_keyboard[:]
                new_keyboard.append(main_keyboard)
                await query.answer('Выберите, как отсортировать для Вас отели', reply_markup=ReplyKeyboardMarkup(keyboard=new_keyboard, resize_keyboard=True,))
            except ValueError:
                await query.answer('Неверная дата, попробуйте еще раз')
        return
    locale = data['locale']
    min_date = data.get('date_from', datetime.date.today().today())
    calendar_locale = 'ru' if locale == 'ru' else 'en'
    result, key, step = DetailedTelegramCalendar(locale=calendar_locale, min_date=min_date).process(query.data)
    if not result and key:
        await query.message.edit_reply_markup(reply_markup=calendar_keyboard(key))
    elif result:
        if first:
            await state.update_data(date_from=result)
            calendar, step = DetailedTelegramCalendar(locale=calendar_locale, min_date=min_date).build()
            await query.message.edit_text('Выберите дату выезда')
            await query.message.edit_reply_markup(reply_markup=calendar_keyboard(calendar))
            await state.set_state(HotelBotForm.date_to)
        else:
            await query.message.delete()
            await state.update_data(date_to=result)
            date_from = data['date_from']
            nights = max((result - date_from).days, 1)
            await state.update_data(nights=nights)
            await state.set_state(HotelBotForm.sort_order)
            main_keyboard = data['main_keyboard']
            new_keyboard = search_keyboard[:]
            new_keyboard.append(main_keyboard)
            await query.message.answer('Выбран период:\n' +
                                       'C  ' + datetime.datetime.strftime(data['date_from'], '%Y-%m-%d') +\
                                       '\nпо  ' + datetime.datetime.strftime(result, '%Y-%m-%d'))
            await query.message.answer('Выберите, как отсортировать для Вас отели', reply_markup=ReplyKeyboardMarkup(keyboard=new_keyboard, resize_keyboard=True,))




async def process_find(message: Message, state: FSMContext):
    def distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        p = pi / 180
        a = abs(0.5 - cos((lat2 - lat1) * p) /2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2)
        return 12742 * asin(sqrt(a))

    await message.delete()
    data = await state.get_data()
    watches = await message.answer_sticker(sticker_id, reply_markup=ReplyKeyboardRemove())
    request = message.text
    if request.startswith('/'):
        request = request[1:]
    else:
        if request.startswith('\U0001F4C8'):
            request = 'lowprice'
        elif request.startswith('\U0001F4C9'):
            request = 'highprice'
        else:
            request = 'bestdeal'
    await state.update_data(order=request)
    city_id = data['city_id']
    max_hotels = config.misc.max_hotels
    check_in = datetime.datetime.strftime(data['date_from'], '%Y-%m-%d')
    check_out = datetime.datetime.strftime(data['date_to'], '%Y-%m-%d')
    adults1 = '1'
    price_min = data.get('lowprice', 0)
    price_max = data.get('highprice', 0)
    currency = config.misc.currency
    if request == 'highprice':
        sort_order = 'PRICE_HIGHEST_FIRST'
    elif request == 'bestdeal':
        sort_order = 'DISTANCE_FROM_LANDMARK'
    else:
        sort_order = 'PRICE'
    locale = hotels_api_locales.get(data['locale'], 'en_US')
    url = "https://hotels4.p.rapidapi.com/properties/list"
    headers = {
        'x-rapidapi-host': "hotels4.p.rapidapi.com",
        'x-rapidapi-key': APIKEY
    }
    querystring = {"destinationId": city_id, "pageNumber": "1", "pageSize": max_hotels, "checkIn": check_in,
                   "checkOut": check_out, "adults1": adults1, "sortOrder": sort_order,
                   "locale": locale, "currency": currency}
    if price_max != 0:
        querystring.update(priceMin=str(price_min), priceMax=str(price_max))
    result = []
    pages = ceil(int(max_hotels)/25)
    with open('hotellist.txt', 'r', encoding='utf-8') as file:
        result = json.load(file)
    # for page in range(1, pages + 1):
    #     querystring['pageNumber'] = str(page)
    #     async with ClientSession() as session:
    #         async with session.get(url, headers=headers, params=querystring) as resp:
    #             if resp.status == 200:
    #                 resp_text = await resp.text()
    #                 resp_json = json.loads(resp_text)
    #                 hotels_list = resp_json['data']['body']['searchResults']['results']
    #                 result.extend(hotels_list)
    if request == 'bestdeal':
        result.sort(key=lambda x: x['ratePlan']['price']['exactCurrent'])
    dates_string = '?q-check-in=' + datetime.date.strftime(data['date_from'], '%Y-%m-%d') + '&q-check-out=' + \
                    datetime.date.strftime(data['date_to'], '%Y-%m-%d')
    lat2 = data['city_lat']
    lon2 = data['city_lon']
    nights = data['nights']
    hotels_list = []
    for hotel in result:
        thumb = hotel["optimizedThumbUrls"]["srpDesktop"]
        url = 'https://hotels.com/ho' + str(hotel['id']) + dates_string
        lat1 = hotel['coordinate'].get('lat', 0)
        lon1 = hotel['coordinate'].get('lon', 0)
        context = {}
        context['title'] = hotel['name']
        context['nights'] = nights
        context['address'] = hotel['address'].get('streetAddress', '') + \
                             hotel['address'].get('extendedAddress', '') + ', ' + \
                             hotel['address'].get('locality', '') + ', ' + \
                             hotel['address'].get('countryName', '')
        context['distance'] = round(distance(lat1, lon1, lat2, lon2), 1)
        price_dict = hotel['ratePlan']['price']
        total_price = price_dict.get('totalPricePerStay', None)
        if total_price:
            context['total_cost'] = total_price
            context['price'] = '$' + str(price_dict['exactCurrent'])
        else:
            context['total_cost'] = '$' + str(price_dict['exactCurrent'])
            context['price'] = '$' + str(round(price_dict['exactCurrent'] / nights, 2))
        hotels_list.append({'thumb': thumb, 'caption': Template(hotel_card).render(context)})

    await state.update_data(hotels_list=hotels_list, hotels_shown=[])
    await state.set_state(HotelBotForm.show_result)
    await watches.delete()
    temp = await message.answer('Готово')
    await command_show(temp, state)





async def process_set_min_price(message:Message, state:FSMContext):
    data = state.get_data()
    config_messages = data['config_messages']
    config_messages.append(message)
    config_messages.append(await message.answer('Введите максимальную цену:'))
    await state.update_data(lowprice=abs(int(message.text)),config_messages=config_messages)
    await state.set_state(HotelBotForm.set_price2)



async def process_set_max_price(message:Message, state:FSMContext):
    data = await state.get_data()
    config_messages = data['config_messages']
    config_messages.append(message)
    lowprice = data.get('lowprice', 0)
    highprice = abs(int(message.text))
    if highprice < lowprice:
        config_messages.append(await message.answer('Неверно заданы границы, попробуйте еще раз...'))
        return
    for mes in config_messages:
        await mes.delete()
    await state.update_data(highprice=abs(int(message.text)), config_messages=[])
    await state.set_state(HotelBotForm.sort_order)


def register_fsm(dp: Router):
    dp.message.register(command_start, Command(commands=["start"]))
    dp.message.register(command_start, F.text.contains('\U0001F3E0'))
    dp.message.register(command_history, F.text.contains('\U0001F4C6'))
    dp.message.register(command_history, Command(commands=['history']))
    dp.message.register(command_config, (F.text.contains('\U0001F527')), (F.from_user.id.in_(ADMINS)))
    dp.message.register(command_config, Command(commands=['config']), (F.from_user.id.in_(ADMINS)))
    dp.message.register(process_city, HotelBotForm.init)
    dp.callback_query.register(process_calendar, DetailedTelegramCalendar.func())
    dp.message.register(process_calendar, F.text.regexp(r'(19|20)\d\d-((0[1-9]|1[012])-(0[1-9]|[12]\d)|(0[13-9]|1[012])-30|(0[13578]|1[02])-31)'))
    dp.message.register(process_find, Command(commands=['lowprice', 'highprice', 'bestdeal']))
    dp.message.register(command_setprices, Command(commands=['setprices']))
    dp.message.register(process_find, F.text.contains('\U0001F4C8'))
    dp.message.register(process_find, F.text.contains('\U0001F4C9'))
    dp.message.register(process_find, F.text.contains('\U0001F44D'))
    dp.message.register(command_setprices, F.text.contains('\U0001F4B5'))
    dp.message.register(process_set_min_price, F.text.isdigit(), HotelBotForm.set_price1)
    dp.message.register(process_set_max_price, F.text.isdigit(), HotelBotForm.set_price2)
    dp.message.register(process_config, HotelBotForm.config)

