import datetime
import json
import logging
from typing import Dict, Any

from aiogram import Router, F, html
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineQuery, \
    InlineKeyboardMarkup
from aiohttp.client import ClientSession
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

from tgbot.keyboards.reply import reply_keyboard, btn_config
from tgbot.misc.aiogoogletrans2.client import Translator
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
    # if city_not_found:
    #     await message.reply('К сожалению, не могу найти такого города, попробуйте еще раз...')
    # else:
    #     await message.reply(city_id)
    #     await message.reply(city_text)
    #     await state.update_data(city_text=city_text)
    #     await state.update_data(city_id=city_id)
    #     await state.update_data(city_lat=latitude)
    #     await state.update_data(city_lon=longitude)
        await state.set_state(HotelBotForm.date_from)
        calendar_locale = 'ru' if message.from_user.language_code == 'ru' else 'en'
        min_date = datetime.date.today()
        calendar, step = DetailedTelegramCalendar().build()
        calendar = calendar.replace(', []', '')
        print(calendar)
        #cal = json.loads(calendar)
        # cal = {"inline_keyboard": [[{"text": 2021, "callback_data": "cbcal_0_s_y_2021_2_17"}, {"text": 2022, "callback_data": "cbcal_0_s_y_2022_2_17"}], [{"text": 2023, "callback_data": "cbcal_0_s_y_2023_2_17"}, {"text": 2024, "callback_data": "cbcal_0_s_y_2024_2_17"}], [{"text": "<<", "callback_data": "cbcal_0_g_y_2018_2_17"}, {"text": " ", "callback_data": "cbcal_0_n"}, {"text": ">>", "callback_data": "cbcal_0_g_y_2026_2_17"}]]}
        cal = {"inline_keyboard": [[{"text": '2021', "callback_data": "cbcal_0_s_y_2021_2_17"}]]}



        await message.answer(text='Выберите {}'.format(LSTEP[step]), reply_markup=cal)


        await message.edit_reply_markup(reply_markup=calendar)

async def process_calendar(query: InlineQuery, state: FSMContext):
    result, key, step = DetailedTelegramCalendar().process(query.data)
    if not result and key:
        await query.answer('Выберите {}'.format(LSTEP[step]),
                                    # query.message.chat.id,
                                    # query.message.message_id,
                                    reply_markup=key)
    elif result:
        if state == HotelBotForm.date_from:
            await state.update_data(date_from=result)
            calendar_locale = 'ru' if query.message.from_user.language_code == 'ru' else 'en'
            min_date = datetime.datetime.strptime(result, '%Y-%m-%d')
            calendar, step = DetailedTelegramCalendar(locale=calendar_locale, min_date=min_date).build()
            await query.answer('Выберите {}'.format(LSTEP[step]),
                                   reply_markup=calendar)
            await state.set_state(HotelBotForm.date_to)
        else:
            await state.update_data(date_from=result)
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
    dp.inline_query.register(process_calendar, (HotelBotForm.date_to or HotelBotForm.date_from))


    #
    # dp.message.register(process_dont_like_write_bots, Form.like_bots and F.text.casefold() == 'no')
    # dp.message.register(process_like_write_bots, Form.like_bots and F.text.casefold() == 'yes')
    # dp.message.register(process_unknown_write_bots, Form.like_bots)
    # dp.message.register(process_language, Form.language)



