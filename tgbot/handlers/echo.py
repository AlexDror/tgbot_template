from aiogram import types, Dispatcher

async def bot_echo(message: types.Message):
    text = [
        "Эхо без состояния.",
        "Сообщение:",
        message.text
    ]

    await message.answer('\n'.join(text))

def register_echo(dp: Dispatcher):
    dp.message.register(bot_echo)
