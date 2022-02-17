import asyncio
from json import load, dumps, loads
from tgbot.misc.aiogoogletrans2.client import Translator


# async def test():
#     text='Хайфа'
#     t = Translator()
#     # tr = await t.translate(text)
#     # print(tr.text)
#     tr = await t.detect(text)
#     print(tr)
#     with open('response_moscow', 'r', encoding='utf-8') as file:
#         resp = loads('{"inline_keyboard": [[{"text": 2021, "callback_data": "cbcal_0_s_y_2021_2_17"}, {"text": 2022, "callback_data": "cbcal_0_s_y_2022_2_17"}], [{"text": 2023, "callback_data": "cbcal_0_s_y_2023_2_17"}, {"text": 2024, "callback_data": "cbcal_0_s_y_2024_2_17"}], [{"text": "<<", "callback_data": "cbcal_0_g_y_2018_2_17"}, {"text": " ", "callback_data": "cbcal_0_n"}, {"text": ">>", "callback_data": "cbcal_0_g_y_2026_2_17"}], []]}')
#     print(dumps(resp, indent=4))
# asyncio.run(test())

import http.client

conn = http.client.HTTPSConnection("hotels4.p.rapidapi.com")

headers = {
    'x-rapidapi-host': "hotels4.p.rapidapi.com",
    'x-rapidapi-key': "24a18de6fdmsh8128e0141c2e59fp11107bjsn9c0879672d39"
    }

conn.request("GET", "/get-meta-data", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))