import asyncio
from json import load, dumps, loads, dump
from tgbot.misc.aiogoogletrans2.client import Translator


async def test():
    text='Хайфа'
    t = Translator()
    # tr = await t.translate(text)
    # print(tr.text)
    tr = await t.detect(text)
    print(tr)
    with open('hotellist.txt', 'r', encoding='utf-8') as file:
        resp = load(file)
    print(dumps(resp, indent=4, ensure_ascii=False))
    with open('hotelutf.txt', 'w', encoding='utf-8') as file:
        dump(resp,file,ensure_ascii=False, indent=4)
asyncio.run(test())

# import http.client
#
# conn = http.client.HTTPSConnection("hotels4.p.rapidapi.com")
#
# headers = {
#     'x-rapidapi-host': "hotels4.p.rapidapi.com",
#     'x-rapidapi-key': "24a18de6fdmsh8128e0141c2e59fp11107bjsn9c0879672d39"
#     }
#
# conn.request("GET", "/get-meta-data", headers=headers)
#
# res = conn.getresponse()
# data = res.read()
#
# print(data.decode("utf-8"))
from geopy import Nominatim
geolocator = Nominatim(user_agent = 'myapps')
location = geolocator.geocode()