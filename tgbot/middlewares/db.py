from aiogram import BaseMiddleware

class DbMiddleware(BaseMiddleware):
    skip_patterns = ["error", "update"]

    async def __call__(self, obj, data, *args):
        pass
        # db_session = obj.bot.get('db')
        # Передаем данные из таблицы в хендлер
        # data['some_model'] = await Model.get()