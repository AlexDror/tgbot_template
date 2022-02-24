"""
Error Handler
"""
import logging
from typing import Any

from aiogram import Router
from aiogram.dispatcher.handler import ErrorHandler


class MyHandler(ErrorHandler):
    """
    Error Handler
    """
    async def handle(self) -> Any:
        logging.exception(
            "Cause unexpected exception %s: %s",
            self.exception_name,
            self.exception_message
        )


def register_error_handler(dp: Router) -> None:
    """
    Register Error Handler
    """
    dp.errors.register(MyHandler)