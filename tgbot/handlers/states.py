"""
Модуль хендлеров и всего, что связано с обработкой событий в боте
"""

import datetime
import json
from difflib import SequenceMatcher
from math import ceil, pi, cos, sqrt, asin
from typing import Any

from geopy import Nominatim
from geopy.adapters import AioHTTPAdapter
from jinja2 import Template
from lxml import html

from aiogram import Router, F
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, \
                          CallbackQuery, InputMedia
from aiohttp.client import ClientSession

from motor.motor_asyncio import AsyncIOMotorClient

from telegram_bot_calendar import DetailedTelegramCalendar
from telegram_bot_pagination import InlineKeyboardPaginator, InlineKeyboardButton

from tgbot.keyboards.inline import calendar_keyboard, hotel_keyboard, city_keyboard
from tgbot.keyboards.reply import reply_keyboard, btn_config, search_keyboard, btn_show_more
from tgbot.misc.aiogoogletrans2.client import Translator
from tgbot.misc.api_locales import hotels_api_locales
from tgbot.misc.templates import hotel_card, query_card, history_card
from tgbot.models.fsm import HotelBotForm
from tgbot.config import config

ADMINS: list = config.tg_bot.admin_ids
APIKEY: str = config.tg_bot.api_token
sticker_id: str = 'CAACAgIAAxkBAAIFaWIQoWdm_f-gOqa-T-wXBsjD5LRmAAJQCwACLw_wBqRaqc_7Le0YIwQ'
date_check_re: str = r'(19|20)\d\d-((0[1-9]|1[012])-(0[1-9]|[12]\d)|(0[13-9]|1[012])-30|'+\
                     '(0[13578]|1[02])-31)'


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
    main_keyboard: list = reply_keyboard[:]
    if message.from_user.id in ADMINS:
        main_keyboard.append(btn_config)
    await state.update_data(main_keyboard=main_keyboard)
    await message.answer('Вас приветствует телеграм-бот туристического агентства TooEasyTravel!\n'
                         'Я попробую найти для Вас комфортный отель по заданным Вами условиям,'
                         'и я уверен, у нас все получится! Если Вы готовы, введите название '
                         'города, в котором Вы планируете остановиться',
                         reply_markup=ReplyKeyboardMarkup(keyboard=[main_keyboard],
                                                          resize_keyboard=True,),)
    await message.delete()


async def command_history(message: Message, state: FSMContext) -> None:
    """
    Хендлер показа истории запросов
    """
    await message.answer('История поиска:')
    connection: AsyncIOMotorClient = AsyncIOMotorClient(config.db.host, int(config.db.port))
    db = connection[config.db.database].collection
    queries = db.find({'user_id': message.from_user.id})
    async for query in queries:
        await message.answer(Template(history_card).render(query,
                                                           ts=datetime.datetime.fromtimestamp),
                             disable_web_page_preview=True)
    connection.close()
    await message.delete()


async def command_config(message: Message, state: FSMContext) -> None:
    """
    Хендлер админского меню конфигурирования параметров бота
    Сохраняет значение состояния, откуда был вызван и список сообщений для последующего удаления
    """
    config_messages: list = [message]
    config_messages.append(await message.answer('Здесь можно настроить дополнительные'
                                                'параметры бота'))
    config_messages.append(await message.answer('Доступны следующие параметры:'))
    variables: list = config.misc.__dict__.keys()
    for var in variables:
        config_messages.append(await message.answer(var + ' = ' + getattr(config.misc, var)))
    config_messages.append(await message.answer('Введите имя параметра и его новое значение '
                                                'через символ "=" без пробелов, '
                                                'окончание ввода - 0'))
    current_state: str = await state.get_state()
    await state.update_data(previous_state=current_state, config_messages=config_messages)
    await state.set_state(HotelBotForm.config)


async def command_setprices(message: Message, state: FSMContext) -> None:
    """
    Хендлер команды установки границ цен отелей
    Сохраняет список сообщений для последующего удаления
    """
    config_messages: list = [message]
    await state.set_state(HotelBotForm.set_price1)
    config_messages.append(await message.answer('Введите минимальную цену: '))
    await state.update_data(config_messages=config_messages)


async def command_show(message: Message, state: FSMContext) -> None:
    """
    Хендлер кнопки "Show more"
    Показывает информацию о каждом найденном отеле
    В зависимости от установленных параметров выводит информацию с картинкой или без,
    квантами заданного размера
    """
    data: dict = await state.get_data()
    hotels_list: list = data.get('hotels_list')
    hotels_shown: list = data.get('hotels_shown')
    hotels_left: int = len(hotels_list) - len(hotels_shown)
    if len(hotels_shown) == 0:
        main_keyboard: list = data.get('main_keyboard')
        reply_kb: ReplyKeyboardMarkup = ReplyKeyboardMarkup(keyboard=[[btn_show_more],
                                                            main_keyboard],
                                                            resize_keyboard=True)
        await message.answer(Template(query_card).render(data), reply_markup=reply_kb)
    counter: int = min(int(config.misc.hotels_per_page), hotels_left)
    for _ in range(counter):
        hotel: dict = hotels_list[len(hotels_shown)]
        if config.misc.show_thumbnails == '1':
            await message.answer_photo(photo=hotel['thumb'], caption=hotel['caption'],
                                       reply_markup=hotel_keyboard(hotel, len(hotels_shown)))
        else:
            await message.answer(text=hotel['caption'],
                                 reply_markup=hotel_keyboard(hotel, len(hotels_shown)))
        hotels_shown.append(hotel['name'])
        connection: AsyncIOMotorClient = AsyncIOMotorClient(config.db.host, int(config.db.port))
        db = connection[config.db.database].collection
        timestamp = data['timestamp']
        db.update_one({'user_id': message.from_user.id, 'timestamp': timestamp},
                  {'$push': {'hotels': (hotel['name'], hotel['url'])}})
        connection.close()
    if len(hotels_list) == len(hotels_shown):
        reply_kb:ReplyKeyboardMarkup = ReplyKeyboardMarkup(keyboard=[data.get('main_keyboard')],
                                                           resize_keyboard=True)
        await message.answer(text='Конец', reply_markup=reply_kb)
    await message.delete()


async def command_help(message: Message, state: FSMContext) -> None:
    """
    Хендлер команды help
    """
    await message.answer('Бог поможет... А я просто бот.')
    await message.delete()


async def process_config(message: Message, state: FSMContext) -> None:
    """
    Хендлер команды config.
    Изменяет параметры конфигурирования, запоминает сообщения
    для последующего удаления, по окончании работы - удаляет.
    """
    data: dict = await state.get_data()
    config_messages: list = data['config_messages']
    config_messages.append(message)
    if message.text == '0':
        for mes in config_messages:
            await mes.delete()
        await state.update_data(config_messages=[])
        await state.set_state(data['previous_state'])
    else:
        try:
            config_messages.append(message)
            values: list = message.text.split('=')
            setattr(config.misc, values[0], values[1])
            config_messages.append(await message.answer('Ok'))
        except Exception as exept:
            config_messages.append(await message.answer(str(exept)))


async def process_city(something: [Message, CallbackQuery], state: FSMContext) -> None:
    """
    Процессор поиска города в базе Hotels.com
    Переводит название города с любого языка на английский,
    определяет географические координаты центра города не от аферистов из Hotels.com,
    а по-честному.
    Сохраняет название города на английском, его id и географические координаты
    """
    data = await state.get_data()
    if isinstance(something, Message):
        message: Message = something
        watches: Message = await message.answer_sticker(sticker_id)
        city_text: str = message.text
        translator: Translator = Translator()
        tr_city_text: Any = await translator.translate(text=city_text)
        if tr_city_text.src == 'bg' and message.from_user.language_code == 'ru':
            # Глюки гугла
            translator:Translator = Translator()
            tr_city_text: Any = await translator.translate(text=city_text, src='ru')
        url:str = "https://hotels4.p.rapidapi.com/locations/v2/search"
        querystring:dict = {"query": tr_city_text.text, "locale": 'en_US', "currency": "USD"}
        headers: dict = {'x-rapidapi-host': "hotels4.p.rapidapi.com",'x-rapidapi-key': APIKEY}
        city_not_found: bool = False
        entities: list = []
        async with ClientSession() as session:
            async with session.get(url, headers=headers, params=querystring) as resp:
                if resp.status == 200:
                    resp_text: str = await resp.text()
                    resp_json: dict = json.loads(resp_text)
                    try:
                        entities = resp_json['suggestions'][0]['entities']
                    except IndexError:
                        city_not_found: bool = True
        if city_not_found:
            await message.answer('К сожалению, не могу найти такого города, попробуйте еще раз...')
        else:
            await watches.delete()
            await message.delete()
            await state.update_data(city_text=city_text, translated_city=tr_city_text.text, entities=entities)

            if len(entities) > 1:
                # # Если городов больше одного
                # temp_cities: dict = {}
                # for entity in resp_json['suggestions'][0]['entities']:
                #     # Угадай, блядь, что задумали пидарасы из hotels.com
                #     # Проверяем точное совпадение названий
                #     temp_cities[entity['destinationId']] = SequenceMatcher(None,
                #                                                            tr_city_text.text.lower(),
                #                                                            entity['name'].lower()).ratio()
                # exact_matches = [key for key, value in temp_cities.items() if value == 1]
                # if len(exact_matches) > 1:
                # # Если точных названий много, уточняем у пользователя
                await message.answer('Уточните название города, пожалуйста:',
                                    reply_markup=city_keyboard(entities))
                return
                # else:
                #     # Если одно точное совпадение
                #     city_id = sorted(temp_cities.items(), key=lambda x: x[1])[-1][0]
            else:
                # Если один город всего
                city_id: str = entities[0]['destinationId']
                longitude: float = entities[0]['longitude']
                latitude: float = entities[0]['latitude']
    else:
        # Прилетел коллбэк
        city_id: str = something.data
        message: Message = something.message
        await message.delete()
        entity: dict = [x for x in data['entities'] if x['destinationId'] == city_id][0]
        longitude: float = entity['longitude']
        latitude: float = entity['latitude']
        await state.update_data(translated_city = str(html.fromstring(entity['caption']).text_content()).strip())
    # Общие действия
    if config.misc.use_geocode != '0':
        location: Any = None
        data = await state.update_data()
        while True:
        # Не всегда сервера геокодинга с первого раза отвечают
            try:
                async with Nominatim(user_agent=config.misc.app_name,
                                    adapter_factory=AioHTTPAdapter, ) as geolocator:
                    location: Any = await geolocator.geocode({'city': data['translated_city']})
                    if location is not None:
                        latitude: float = location.latitude
                        longitude: float = location.longitude
                        break
            except Exception:
                pass
    await state.update_data(city_id=city_id)
    await state.update_data(city_lat=latitude)
    await state.update_data(city_lon=longitude)
    await state.set_state(HotelBotForm.date_from)
    calendar_locale = 'ru' if message.from_user.language_code == 'ru' else 'en'
    min_date = datetime.date.today()
    calendar, step = DetailedTelegramCalendar(locale=calendar_locale, min_date=min_date).build()
    await message.answer(text='Выберите дату заезда', reply_markup=calendar_keyboard(calendar))


async def process_calendar(query: [CallbackQuery, Message], state: FSMContext) -> None:
    """
    Процессор календаря, а также ручного ввода дат.
    Сохраняет значения дат въезда и выезда из отеля, количество ночей.
    """
    async def finish(message, date_1, date_2) -> None:
        """
        Вспомогательная процедура
        """
        await state.update_data(date_to=date_1)
        nights: int = max((date_1 - date_2).days, 1)
        await state.update_data(nights=nights)
        await state.set_state(HotelBotForm.sort_order)
        main_keyboard: list = data['main_keyboard']
        new_keyboard: list = search_keyboard[:]
        new_keyboard.append(main_keyboard)
        await message.answer('Выберите, как отсортировать для Вас отели',
                             reply_markup=ReplyKeyboardMarkup(keyboard=new_keyboard,
                                                              resize_keyboard=True, ))

    first: bool = await state.get_state() == 'HotelBotForm:date_from'
    data: dict = await state.get_data()
    if isinstance(query, Message):
        # Если ручной ввод
        if first:
            try:
                date_from = datetime.datetime.strptime(query.text, '%Y-%m-%d')
                if date_from < datetime.date.today():
                    raise ValueError
                await state.update_data(date_from=date_from)
                await state.set_state(HotelBotForm.date_to)
            except ValueError:
                await query.answer('Неверная дата, попробуйте еще раз')
            finally:
                await query.delete()
        else:
            try:
                date_to = datetime.datetime.strptime(query.text, '%Y-%m-%d')
                date_from = data['date_from']
                if date_to < date_from:
                    raise ValueError
                await finish(query, date_to, date_from)
            except ValueError:
                await query.answer('Неверная дата, попробуйте еще раз')
            await query.delete()
    else:
        locale: str = data['locale']
        min_date = data.get('date_from', datetime.date.today())
        calendar_locale: str = 'ru' if locale == 'ru' else 'en'
        result, key, step = DetailedTelegramCalendar(locale=calendar_locale,
                                                     min_date=min_date).process(query.data)
        if not result and key:
            await query.message.edit_reply_markup(reply_markup=calendar_keyboard(key))
        elif result:
            if first:
                await state.update_data(date_from=result)
                calendar, step = DetailedTelegramCalendar(locale=calendar_locale,
                                                          min_date=min_date).build()
                await query.message.edit_text('Выберите дату выезда')
                await query.message.edit_reply_markup(reply_markup=calendar_keyboard(calendar))
                await state.set_state(HotelBotForm.date_to)
            else:
                await query.message.delete()
                date_from = data['date_from']
                await finish(query.message, result, date_from)


async def process_find(message: Message, state: FSMContext) -> None:
    """
    Процессор поиска отелей.
    Сохраняет список с данными отелей.
    """
    def distance() -> float:
        """
        Вычисление расстояния до центра города по усовершенствованной формуле гаверсинусов
        """
        p: float = pi / 180
        a: float = abs(0.5 - cos((lat2 - lat1) * p) / 2 + cos(lat1 * p) *\
                     cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2)
        return 12742 * asin(sqrt(a))

    data: dict = await state.get_data()
    watches: Message = await message.answer_sticker(sticker_id, reply_markup=ReplyKeyboardRemove())
    # Способ сортировки
    request: str = message.text
    if request.startswith('/'):
        request: str = request[1:]
    else:
        if request.startswith('\U0001F4C8'):
            request: str = 'lowprice'
        elif request.startswith('\U0001F4C9'):
            request: str = 'highprice'
        else:
            request: str = 'bestdeal'
    await state.update_data(order=request)
    city_id: str = data['city_id']
    max_hotels: str = config.misc.max_hotels
    page_size: str = str(min(int(max_hotels), 25))
    check_in = datetime.datetime.strftime(data['date_from'], '%Y-%m-%d')
    check_out = datetime.datetime.strftime(data['date_to'], '%Y-%m-%d')
    adults1: str = '1'
    price_min: int = data.get('lowprice', 0)
    price_max: int = data.get('highprice', 0)
    currency: str = config.misc.currency
    if request == 'highprice':
        sort_order: str = 'PRICE_HIGHEST_FIRST'
        sort_comment: str = 'по убыванию цены'
    elif request == 'bestdeal':
        sort_order: str = 'DISTANCE_FROM_LANDMARK'
        sort_comment: str = 'оптимум по цене и расстоянию от центра'
    else:
        sort_order: str = 'PRICE'
        sort_comment: str = 'по возрастанию цены'
    locale: str = hotels_api_locales.get(data['locale'], 'en_US')
    url: str = "https://hotels4.p.rapidapi.com/properties/list"
    headers: dict = {'x-rapidapi-host': "hotels4.p.rapidapi.com", 'x-rapidapi-key': APIKEY}
    querystring: dict = {"destinationId": city_id, "pageNumber": "1",
                         "pageSize": page_size, "checkIn": check_in,"checkOut": check_out,
                         "adults1": adults1, "sortOrder": sort_order, "locale": locale,
                         "currency": currency}
    if price_max != 0:
        querystring.update(priceMin=str(price_min), priceMax=str(price_max))
    result: list = []
    pages: int = ceil(int(max_hotels)/25)
    for page in range(1, pages + 1):
        querystring['pageNumber']: str = str(page)
        async with ClientSession() as session:
            async with session.get(url, headers=headers, params=querystring) as resp:
                if resp.status == 200:
                    resp_text: str = await resp.text()
                    resp_json: dict = json.loads(resp_text)
                    hotels_list: list = resp_json['data']['body']['searchResults']['results']
                    result.extend(hotels_list)
    if request == 'bestdeal':
        result.sort(key=lambda x: x['ratePlan']['price']['exactCurrent'])
    dates_string: str = '?q-check-in=' + datetime.date.strftime(data['date_from'], '%Y-%m-%d') + \
                        '&q-check-out=' + datetime.date.strftime(data['date_to'], '%Y-%m-%d')
    lat2: float = data['city_lat']
    lon2: float = data['city_lon']
    nights: int = data['nights']
    hotels_list: list = []
    for hotel in result:
        thumb: str = hotel["optimizedThumbUrls"]["srpDesktop"]
        url: str = 'https://hotels.com/ho' + str(hotel['id']) + dates_string
        lat1: float = hotel['coordinate'].get('lat', 0)
        lon1: float = hotel['coordinate'].get('lon', 0)
        context = {'title': hotel['name'], 'nights': nights, 'distance': round(distance(), 1),
                   'address': hotel['address'].get('streetAddress', '') +
                              hotel['address'].get('extendedAddress', '') + ', ' +
                              hotel['address'].get('locality', '') + ', ' +
                              hotel['address'].get('countryName', '')}
        price_dict: dict = hotel['ratePlan']['price']
        total_price: str = price_dict.get('totalPricePerStay', None)
        if total_price:
            context['total_cost']: str = total_price
            context['price']: str = config.misc.currency_sym + str(price_dict['exactCurrent'])
        else:
            context['total_cost']: str = config.misc.currency_sym + str(price_dict['exactCurrent'])
            context['price']: str = '$' + str(round(price_dict['exactCurrent'] / nights, 2))
        hotels_list.append({'thumb': thumb, 'caption': Template(hotel_card).render(context),
                            'name': hotel['name'], 'id': hotel['id'], 'url': url,
                            'longitude': lon1, 'latitude': lat1, 'address': context['address']})

    await state.update_data(hotels_list=hotels_list, hotels_shown=[], sort_comment=sort_comment,
                            lowprice=price_min, highprice=price_max, cur_sym=config.misc.currency_sym)
    await state.set_state(HotelBotForm.show_result)
    await message.delete()
    await watches.delete()
    timestamp = datetime.datetime.now().timestamp()
    connection: AsyncIOMotorClient = AsyncIOMotorClient(config.db.host, int(config.db.port))
    db = connection[config.db.database].collection
    db.insert_one({'user_id':message.from_user.id,
               'timestamp':timestamp,
               'city_text':data['city_text'],
               'date_from':datetime.date.strftime(data['date_from'], '%Y-%m-%d'),
               'date_to':datetime.date.strftime(data['date_to'], '%Y-%m-%d'),
               'sort_comment':sort_comment,
               'lowprice':price_min,
               'high_price':price_max,
               'cur_sym':config.misc.currency_sym,
               'hotels':[]})
    connection.close()
    await state.update_data(db=db, timestamp=timestamp)
    temp: Message = await message.answer('Готово')
    await command_show(temp, state)


async def hotel_callback(query: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик инлайн-кнопок отеля.
    Сохраняет фотографии отеля, если их нет в данных FSM.
    Показывает сайт и карту с расположением отеля
    """
    data: dict = await state.get_data()
    parse: list = query.data.split('#')
    hotel: dict = data['hotels_list'][int(parse[1])]
    if parse[0] == 'map':
        if config.misc.show_venue == '1':
            await query.message.answer_venue(latitude=hotel['latitude'],
                                             longitude=hotel['longitude'],
                                             title=hotel['name'],
                                             address=hotel['address'])
        else:
            await query.message.answer_location(latitude=hotel['latitude'],
                                                longitude=hotel['longitude'])
    elif parse[0] == 'photo':
        albums: dict = data.get('albums', {})
        album: list = albums.get(hotel['id'], None)
        if album is None:
            album: list = []
            url: str = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
            querystring: dict = {"id": str(hotel['id'])}
            headers: dict = {'x-rapidapi-host': "hotels4.p.rapidapi.com", 'x-rapidapi-key': APIKEY}
            async with ClientSession() as session:
                async with session.get(url, headers=headers, params=querystring) as resp:
                    if resp.status == 200:
                        resp_text: str = await resp.text()
                        resp_json: dict = json.loads(resp_text)
                        pictures: list = resp_json.get('hotelImages', [])
                        for picture in pictures:
                            url: str = picture.get('baseUrl')
                            size: str = picture['sizes'][0].get('suffix', 'z')
                            album.append(url.replace('{size}', size))
            albums[hotel['id']]: list = album
            await state.update_data(albums=albums, album=album)
        await state.set_state(HotelBotForm.show_photo)
        await start_photo(query.message, state)


async def start_photo(message: Message, state: FSMContext) -> None:
    """
    Старт пагинатора с картинками
    """
    data: dict = await state.get_data()
    album: list = data['album']
    pages: int = len(album)
    paginator: InlineKeyboardPaginator = InlineKeyboardPaginator(page_count=pages,
                                                                 data_pattern='picture#{page}')
    paginator.add_after(InlineKeyboardButton('\U0000274C Закрыть', callback_data='back'))
    await state.update_data(photo_page=1)
    await message.answer_photo(album[0], reply_markup=calendar_keyboard(paginator.markup))


async def photo_page_callback(query: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик действий пагинатора с картинками
    """
    if query.data == 'back':
        await query.message.delete()
        await state.update_data(photo_page=None)
        await state.set_state(HotelBotForm.show_result)
    else:
        data: dict = await state.get_data()
        album: list = data['album']
        await query.answer()
        page: int = int(query.data.split('#')[1])
        if data['photo_page'] != page:
            pages: int = len(album)
            paginator: InlineKeyboardPaginator = InlineKeyboardPaginator(page_count=pages,
                                                                         current_page=page,
                                                                         data_pattern='picture#{page}')
            paginator.add_after(InlineKeyboardButton('\U0000274C Закрыть', callback_data='back'))
            await state.bot.edit_message_media(media=InputMedia(type='photo',
                                                                  media=album[page-1]),
                                               chat_id=query.message.chat.id,
                                               message_id=query.message.message_id,
                                               reply_markup=calendar_keyboard(paginator.markup))
            await state.update_data(photo_page=page)


async def process_set_min_price(message: Message, state: FSMContext) -> None:
    """
    Процессор ввода минимальной цены
    """
    data: dict = await state.get_data()
    config_messages: list = data['config_messages']
    config_messages.append(message)
    config_messages.append(await message.answer('Введите максимальную цену:'))
    await state.update_data(lowprice=abs(int(message.text)), config_messages=config_messages)
    await state.set_state(HotelBotForm.set_price2)


async def process_set_max_price(message: Message, state: FSMContext) -> None:
    """
    Процессор ввода максимальной цены.
    По окончании работы чистит сообщения.
    """
    data: dict = await state.get_data()
    config_messages: list = data['config_messages']
    config_messages.append(message)
    lowprice: int = data.get('lowprice', 0)
    highprice: int = abs(int(message.text))
    if highprice < lowprice:
        config_messages.append(await message.answer('Неверно заданы границы, попробуйте еще раз'))
        return
    for mes in config_messages:
        await mes.delete()
    await state.update_data(highprice=abs(int(message.text)), config_messages=[])
    await state.set_state(HotelBotForm.sort_order)


async def plugger(message: Message, state: FSMContext) -> None:
    """
    Затычка для непонятных действий пользователя
    """
    await message.delete()
    await message.answer('Непонятная команда, попробуйте ещё...')

def register_fsm(dp: Router) -> None:
    """
    Регистрация всех хендлеров
    """
    dp.callback_query.register(process_city, HotelBotForm.init)
    dp.callback_query.register(process_calendar, DetailedTelegramCalendar.func())
    dp.callback_query.register(hotel_callback, HotelBotForm.show_result)
    dp.callback_query.register(photo_page_callback, HotelBotForm.show_photo)
    dp.message.register(command_start, Command(commands=["start"]))
    dp.message.register(command_start, F.text.startswith('\U0001F3E0'))
    dp.message.register(command_help, Command(commands=["help"]))
    dp.message.register(command_history, F.text.startswith('\U0001F4C6'))
    dp.message.register(command_history, Command(commands=['history']))
    dp.message.register(command_config, (F.text.contains('\U0001F527')), (F.from_user.id.in_(ADMINS)))
    dp.message.register(command_config, Command(commands=['config']), (F.from_user.id.in_(ADMINS)))
    dp.message.register(command_setprices, Command(commands=['setprices']))
    dp.message.register(command_setprices, F.text.startswith('\U0001F4B5'))
    dp.message.register(command_show, F.text.startswith('\U000023E9'))
    dp.message.register(process_city, HotelBotForm.init)
    dp.message.register(process_calendar, F.text.regexp(date_check_re))
    dp.message.register(process_find, Command(commands=['lowprice', 'highprice', 'bestdeal']))
    dp.message.register(process_find, F.text.startswith('\U0001F4C8'))
    dp.message.register(process_find, F.text.startswith('\U0001F4C9'))
    dp.message.register(process_find, F.text.startswith('\U0001F44D'))
    dp.message.register(process_set_min_price, F.text.isdigit(), HotelBotForm.set_price1)
    dp.message.register(process_set_max_price, F.text.isdigit(), HotelBotForm.set_price2)
    dp.message.register(process_config, HotelBotForm.config)
    dp.message.register(plugger)
