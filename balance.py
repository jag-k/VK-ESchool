import asyncio
import threading
import ujson
from queue import Queue
from sys import stderr

import aiohttp
from bs4 import BeautifulSoup as bs

from tinydb import TinyDB, Query
from aiotinydb import AIOTinyDB

# Constants and Types

SLEEP_TIME = 30
DB_NAME = "cards_data.json"
BALANCE_UPDATE = "bl"


# Functions

async def get_balance(session, card):
    print(f"\x1b[33mSearch {card}\x1b[0m")
    try:
        async with session.post("http://xn--58-6kc3bfr2e.xn--p1ai/ajax/",
                                data={"card": card, "act": "FreeCheckBalance"},
                                headers={
                                    "Content-Type": "application/x-www-form-urlencoded"
                                }) as response:
            if response.status == 200:
                raw = await response.read()
                raw = raw.strip()
                # print(str(raw, encoding='utf-8'))
                try:
                    result = ujson.decode(raw)
                    if result.get('type', "error") == "error":
                        print(f"Card {card} not found", file=stderr)

                    if result and result.get("type") == "balance":
                        soup = bs(result.get("text"), features="lxml")
                        balances = map(lambda x: x.find("span").contents[0], soup.find_all("div", {"class": "name"}))
                        balances_value = map(lambda x: float(x.find("span").contents[0].strip(" руб.")),
                                             soup.find_all("div", {"class": "residue"}))

                        return {"card": card, "balance": dict(zip(balances, balances_value))}
                    return result

                except ValueError:
                    print(f'Card {card} is not JSON', file=stderr)
                    return {}
    except aiohttp.ClientConnectionError:
        print(f"Card {card} connection error", file=stderr)
        return {}


async def process_card(session, card, cards_data, q):
    res = await get_balance(session, card)  # type: dict
    if res and not res.get("type") == "error":
        if res["balance"] != cards_data.get(Query().card == card)['balance']:
            q.put_nowait({
                "type": BALANCE_UPDATE,
                "new_balance": res,
                "old_balance": cards_data.get(Query().card == card)
            })

        async with AIOTinyDB(DB_NAME) as db:
            db.upsert(res, Query().card == card)
        return res


async def check_cards_balance(q):
    async with aiohttp.ClientSession() as session:
        while True:

            async with AIOTinyDB(DB_NAME) as db:

                tasks = [
                    asyncio.ensure_future(
                        process_card(session, card['card'], db, q)
                    ) for card in db
                ]
                res = await asyncio.gather(*tasks)
                print(res)
                await asyncio.sleep(SLEEP_TIME)


def balanced_thread(q: Queue):
    ioloop = asyncio.new_event_loop()
    ioloop.run_until_complete(check_cards_balance(q))
    ioloop.close()


def main():
    q = Queue()
    balance = threading.Thread(target=balanced_thread, args=(q, ))
    balance.start()

    q.join()


if __name__ == '__main__':
    main()
