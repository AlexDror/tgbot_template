"""
Хендлеры меню конфигурирования бота
"""
from aiogram import F, Router
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message

from tgbot.config import load_config, config, i18n
from tgbot.models.fsm import HotelBotForm

_ = i18n.gettext
ADMINS = load_config('.env').tg_bot.admin_ids


async def command_config(message: Message, state: FSMContext) -> None:
    """
    Хендлер админского меню конфигурирования параметров бота.
    Сохраняет значение состояния, откуда был вызван и список сообщений для последующего удаления
    """
    config_messages: list = [message]
    config_messages.append(await message.answer(_('Здесь можно настроить дополнительные'
                                                 'параметры бота')))
    config_messages.append(await message.answer(_('Доступны следующие параметры:')))
    variables: list = config.misc.__dict__.keys()
    for var in variables:
        config_messages.append(await message.answer(var + ' = ' + getattr(config.misc, var)))
    config_messages.append(await message.answer(_('Введите имя параметра и его новое значение '
                                                 'через символ "=" без пробелов, '
                                                 'окончание ввода - 0')))
    current_state: str = await state.get_state()
    await state.update_data(previous_state=current_state, config_messages=config_messages)
    await state.set_state(HotelBotForm.config)


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


def register_admin_handlers(dp: Router) -> None:
    dp.message.register(command_config, (F.text.contains('\U0001F527')), (F.from_user.id.in_(ADMINS)))
    dp.message.register(command_config, Command(commands=['config']), (F.from_user.id.in_(ADMINS)))
    dp.message.register(process_config, HotelBotForm.config)

