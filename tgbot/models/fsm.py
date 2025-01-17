"""
Состояния конечного автомата бота
"""
from aiogram.dispatcher.fsm.state import StatesGroup, State

class HotelBotForm(StatesGroup):
    init = State()
    date_from = State()
    date_to = State()
    sort_order = State()
    set_price1 = State()
    set_price2 = State()
    show_result = State()
    show_photo = State()
    config = State()
