import asyncio

from tgbot.misc.aiogoogletrans2.client import Translator


async def test():
    text='Нью-Йорк'
    t = Translator()
    tr = await t.translate(text)
    print(tr.text)

asyncio.run(test())