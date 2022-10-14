import asyncio
from curses import noecho
from tkinter.tix import Tree
import time, requests
from tracemalloc import stop
from bfxapi.client import Client
from ftxclient import FtxClient
import datetime

log_path = "rate.txt"

while True:
    f = open(log_path, "a", encoding="utf-8")
    # print('===========================================================\n',datetime.datetime.now())
    fUSD_url = "https://api-pub.bitfinex.com/v2/book/fUSD/P2"
    bfx_r = requests.get(fUSD_url)
    latest = bfx_r.json()[0][0]
    data = bfx_r.json()
    # print('\n當前BFX掛單借入利率:{}%'.format(latest*365*100))
    # print('當前BFX掛單貸出利率:{}%\n'.format(bfx_r.json()[26][0]*365*100))

    if bfx_r.json()[26][0] * 365 * 100 > 15:
        for k in range(3):
            fUSD_url = "https://api-pub.bitfinex.com/v2/book/fUSD/P2"
            bfx_r = requests.get(fUSD_url)
            latest = bfx_r.json()[0][0]
            data = bfx_r.json()
            print(
                "{}\toffer利率吃到{}".format(
                    datetime.datetime.now(), bfx_r.json()[26][0] * 365 * 100
                )
            )
            f.write(
                "=================================================================\n"
            )
            f.write(
                "{}\n\t當前利率{}\n".format(
                    datetime.datetime.now(), bfx_r.json()[26][0] * 365 * 100
                )
            )
            for i in bfx_r.json()[24:]:
                f.write(",{}\n".format(i))
            time.sleep(1)

    time.sleep(2)

t = asyncio.ensure_future(get_funding_offer())
asyncio.get_event_loop().run_until_complete(t)
