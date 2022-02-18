import datetime
import json
import logging
from typing import Dict, Any

from aiogram import Router, F, html
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineQuery, \
    InlineKeyboardMarkup, CallbackQuery
from aiohttp.client import ClientSession
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

from tgbot.keyboards.inline import calendar_keyboard
from tgbot.keyboards.reply import reply_keyboard, btn_config, search_keyboard
from tgbot.misc.aiogoogletrans2.client import Translator
from tgbot.misc.api_locales import hotels_api_locales
from tgbot.models.fsm import Form, HotelBotForm
from tgbot.config import config

ADMINS = config.tg_bot.admin_ids
APIKEY = config.tg_bot.api_token

async def command_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(HotelBotForm.init)
    await state.update_data(locale=message.from_user.language_code)
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


async def command_history(message: Message, state: FSMContext):
    await message.answer('Здесь будет история поисков')
    await message.delete()


async def command_config(message: Message, state: FSMContext):
    await message.answer('Здесь будет настройка')
    await message.delete()


async def process_city(message: Message, state: FSMContext):
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
    latitude = 55.55918638239373
    longitude = 37.363508158852
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


async def get_hotels_list(state: FSMContext) -> list:
    data = await state.get_data()
    city_id = data['city_id']
    max_hotels = config.misc.max_hotels
    check_in = datetime.date.strftime(data['date_from'], '%Y-%m-%d')
    check_out = datetime.date.strftime(data['date_to'], '%Y-%m-%d')
    adults1 = '1'
    price_min = data.get('lowprice', 0)
    price_max = data.get('highprice', 0)
    currency = 'USD'
    order = data.get('order', 'lowprice')
    if order == 'highprice':
        sort_order = 'PRICE_HIGHEST_FIRST'
    elif order == 'bestdeal':
        sort_order = 'DISTANCE_FROM_LANDMARK'
    else:
        sort_order = 'PRICE'
    locale = hotels_api_locales.get(data['locale'], 'en_US')
    url = "https://hotels4.p.rapidapi.com/properties/list"

    querystring = {"destinationId": city_id, "pageNumber": "1", "pageSize": max_hotels, "checkIn": check_in,
                   "checkOut": check_out, "adults1": adults1, "priceMin": "20", "priceMax": "3000", "sortOrder": sort_order,
                   "locale": locale, "currency": currency}
    if price_max != 0:
        querystring.update(priceMin=str(price_min), priceMax=str(price_max))

    headers = {
        'x-rapidapi-host': "hotels4.p.rapidapi.com",
        'x-rapidapi-key': "24a18de6fdmsh8128e0141c2e59fp11107bjsn9c0879672d39"
    }
    async with ClientSession() as session:
        async with session.get(url, headers=headers, params=querystring) as resp:
            if resp.status == 200:
                resp_text = await resp.text()
                resp_json = json.loads(resp_text)
            else:
                return
    hotels_list = resp_json['data']['body']['searchResults']['results']
    if order == 'bestdeal':
        hotels_list.sort(key=lambda x: x['ratePlan']['price']['exactCurrent'])
    await state.update_data(hotels_list=hotels_list)
    return hotels_list


def message_hotel(hotel: dict) -> tuple:
    pass


async def process_calendar(query: [CallbackQuery, Message], state: FSMContext):
    first = await state.get_state() == 'HotelBotForm:date_from'
    data = await state.get_data()
    if isinstance(query, Message):
        print('gjgfk')
        if first:
            try:
                date_from = datetime.date.strptime(query.text, '%Y-%m-%d')
                if date_from < datetime.date.today():
                    raise ValueError
                await state.update_data(date_from=datetime.date.strptime(query.text, '%Y-%m-%d'))
                await state.set_state(HotelBotForm.date_to)
            except ValueError:
                await query.answer('Неверная дата, попробуйте еще раз')
        else:
            try:
                date_to = datetime.datetime.strptime(query.text, '%Y-%m-%d')
                date_from = data['date_from']
                if date_to < date_from:
                    raise ValueError
                await state.update_data(date_to=datetime.date.strptime(query.text, '%Y-%m-%d'))
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
            await state.set_state(HotelBotForm.sort_order)
            main_keyboard = data['main_keyboard']
            new_keyboard = search_keyboard[:]
            new_keyboard.append(main_keyboard)
            await query.message.answer('Выбран период:\n' +
                                       'C  ' + datetime.datetime.strftime(data['date_from'], '%Y-%m-%d') +\
                                       '\nпо  ' + datetime.datetime.strftime(result, '%Y-%m-%d'))
            await query.message.answer('Выберите, как отсортировать для Вас отели', reply_markup=ReplyKeyboardMarkup(keyboard=new_keyboard, resize_keyboard=True,))


async def process_lowprice(message: Message, state: FSMContext):
    message.delete()
    await state.update_data(order='lowprice')
    data = await state.get_data()
    main_keyboard = data['main_keyboard']
    await message.answer('Начинаю искать...', reply_markup=ReplyKeyboardMarkup(keyboard=[main_keyboard], resize_keyboard=True,),)
    await state.set_state(HotelBotForm.show_result)

async def process_highprice(message: Message, state: FSMContext):
    message.delete()
    await state.update_data(order='highprice')
    data = await state.get_data()
    main_keyboard = data['main_keyboard']
    await message.answer('Начинаю искать...', reply_markup=ReplyKeyboardMarkup(keyboard=[main_keyboard], resize_keyboard=True,),)
    await state.set_state(HotelBotForm.show_result)

async def process_bestdeal(message: Message, state: FSMContext):
    message.delete()
    await state.update_data(order='bestdeal')
    data = await state.get_data()
    main_keyboard = data['main_keyboard']
    await message.answer('Начинаю искать...', reply_markup=ReplyKeyboardMarkup(keyboard=[main_keyboard], resize_keyboard=True,),)
    await state.set_state(HotelBotForm.show_result)


async def process_setprices(message:Message, state:FSMContext):
    message.delete()
    await state.set_state(HotelBotForm.set_price1)
    await message.answer('Введите минимальную цену: ')

async def process_set_min_price(message:Message, state:FSMContext):
    await state.update_data(lowprice=abs(int(message.text)))
    await state.set_state(HotelBotForm.set_price2)
    await message.answer('Введите максимальную цену:')

async def process_set_max_price(message:Message, state:FSMContext):
    data = await state.get_data()
    lowprice = data.get('lowprice', 0)
    highprice = abs(int(message.text))
    if highprice < lowprice:
        await message.answer('Неверно заданы границы, попробуйте еще раз...')
        return
    await state.update_data(highprice=abs(int(message.text)))
    await state.set_state(HotelBotForm.sort_order)




async def process_name(message: Message, state: FSMContext):
    await state.update_data(name = message.text)
    await state.set_state(Form.like_bots)
    await message.answer(
        f"Nice to meet you, {html.quote(message.text)}!\nDid you like to write bots?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Yes"), KeyboardButton(text="No"),]],
            resize_keyboard=True,
        ),
    )


async def process_dont_like_write_bots(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    await message.answer(
        "Not bad not terrible.\nSee you soon.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await show_summary(message=message, data=data, positive=False)


async def process_like_write_bots(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.language)
    await message.reply(
        "Cool! I'm too!\nWhat programming language did you use for it?",
        reply_markup=ReplyKeyboardRemove(),
    )


async def process_unknown_write_bots(message: Message, state: FSMContext) -> None:
    await message.reply("I don't understand you :(")


async def process_language(message: Message, state: FSMContext) -> None:
    data = await state.update_data(language=message.text)
    await state.clear()
    text = (
        "Thank for all! Python is in my hearth!\nSee you soon."
        if message.text.casefold() == "python"
        else "Thank for information!\nSee you soon."
    )
    await message.answer(text)
    await show_summary(message=message, data=data)


async def show_summary(message: Message, data: Dict[str, Any], positive: bool = True) -> None:
    name = data["name"]
    language = data.get("language", "<something unexpected>")
    text = f"I'll keep in mind that, {html.quote(name)}, "
    text += (
        f"you like to write bots with {html.quote(language)}."
        if positive
        else "you don't like to write bots, so sad..."
    )
    await message.answer(text=text, reply_markup=ReplyKeyboardRemove())


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
    dp.message.register(process_lowprice, Command(commands=['lowprice']))
    dp.message.register(process_highprice, Command(commands=['highprice']))
    dp.message.register(process_bestdeal, Command(commands=['bestdeal']))
    dp.message.register(process_setprices, Command(commands=['setprices']))
    dp.message.register(process_lowprice, F.text.contains('\U0001F4C8'))
    dp.message.register(process_highprice, F.text.contains('\U0001F4C9'))
    dp.message.register(process_bestdeal, F.text.contains('\U0001F44D'))
    dp.message.register(process_setprices, F.text.contains('\U0001F4B5'))
    dp.message.register(process_set_min_price, F.text.isdigit(), HotelBotForm.set_price1)
    dp.message.register(process_set_max_price, F.text.isdigit(), HotelBotForm.set_price2)


    #
    # dp.message.register(process_dont_like_write_bots, Form.like_bots and F.text.casefold() == 'no')
    # dp.message.register(process_like_write_bots, Form.like_bots and F.text.casefold() == 'yes')
    # dp.message.register(process_unknown_write_bots, Form.like_bots)
    # dp.message.register(process_language, Form.language)



