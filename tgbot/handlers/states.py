import logging
from typing import Dict, Any

from aiogram import Router, F, html
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton

from tgbot.models.fsm import Form


async def command_start(message: Message, state: FSMContext):
    await state.set_state(Form.name)
    await message.answer("Hi there! What's your name?", reply_markup=ReplyKeyboardRemove(),)


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
            keyboard=[
                [
                    KeyboardButton(text="Yes"),
                    KeyboardButton(text="No"),
                ]
            ],
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
    dp.message.register(process_name, Form.name)
    dp.message.register(process_dont_like_write_bots, Form.like_bots and F.text.casefold() == 'no')
    dp.message.register(process_like_write_bots, Form.like_bots and F.text.casefold() == 'yes')
    dp.message.register(process_unknown_write_bots, Form.like_bots)
    dp.message.register(process_language, Form.language)



