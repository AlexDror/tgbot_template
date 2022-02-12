import json
import logging
from typing import Dict, Any

from aiogram import Router, F, html
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiohttp.client import ClientSession

from bot import config
from tgbot.keyboards.reply import reply_keyboard
from tgbot.misc.aiogoogletrans2.client import Translator
from tgbot.models.fsm import Form, HotelBotForm

APIKEY = config.tg_bot.api_token
ADMINS = config.tg_bot.admin_ids

async def command_start(message: Message, state: FSMContext):
    await state.set_state(HotelBotForm.init)
    await state.update_data(locale=message.from_user.language_code)
    await message.answer('Вас приветствует телеграм-бот туристического агентства TooEasyTravel!\n'
                         'Я попробую найти для Вас комфортный отель по заданным Вами условиям,'
                         'и я уверен, у нас все получится! Если Вы готовы, введите название'
                         'города, в котором Вы планируете остановиться',
                         reply_markup=ReplyKeyboardMarkup(keyboard=[reply_keyboard],
                                                          resize_keyboard=True,),)


async def process_city(message: Message, state: FSMContext):
    city_text = message.text
    translator = Translator()
    tr_city_text = await translator.translate(text=city_text)
    city_text = tr_city_text.text
    url = "https://hotels4.p.rapidapi.com/locations/v2/search"
    querystring = {"query": city_text, "locale": 'en_US', "currency": "USD"}
    headers = {
        'x-rapidapi-host': "hotels4.p.rapidapi.com",
        'x-rapidapi-key': APIKEY
    }
    city_not_found = False
    async with ClientSession() as session:
        async with session.get(url, headers=headers, params=querystring) as resp:
            if resp.status == 200:
                resp_text = await resp.text()
                resp_json = json.loads(resp_text)
                try:
                    city_id = resp_json['suggestions'][0]['entities'][0]['destinationId']
                except IndexError:
                    city_not_found = True
    if city_not_found:
        await message.reply('К сожалению, не могу найти такого города, попробуйте еще раз...')
    else:
        await message.reply(city_id)
        await message.reply(city_text)
        await state.update_data(city_text=city_text, city_id=city_id)
        await state.set_state(HotelBotForm.date_from)
        # Calendar

async def cancel_handler(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    logging.info("Cancelling state %r", current_state)
    await state.clear()
    await message.answer('Cancelled.', reply_markup=ReplyKeyboardRemove(),)

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
    dp.message.register(cancel_handler, Command(commands=['cancel']) or F.text.casefold() == 'cancel')
    dp.message.register(process_city, HotelBotForm.init)
    dp.message.register(process_dont_like_write_bots, Form.like_bots and F.text.casefold() == 'no')
    dp.message.register(process_like_write_bots, Form.like_bots and F.text.casefold() == 'yes')
    dp.message.register(process_unknown_write_bots, Form.like_bots)
    dp.message.register(process_language, Form.language)



