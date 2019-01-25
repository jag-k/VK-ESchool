import asyncio
import threading
import ujson
from queue import Queue
from sys import stderr

import aiohttp
from bs4 import BeautifulSoup as bs
import aiofiles as aiof

cards_data = ujson.load(open("cards_data.json"))  # type: dict

# Constants and Types

SLEEP_TIME = 30
BALANCE_UPDATE = "bl"


# Functions

async def get_balance(session, card):
    print(f"Search {card}")
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
                    return result
                except ValueError:
                    print(f'Card {card} is not JSON', file=stderr)
                    return {}
    except aiohttp.ClientConnectionError:
        print(f"Card {card} connection error", file=stderr)
        return {}


async def process_card(session, card, q):
    card_data = await get_balance(session, card)  # type: dict
    if cards_data and card_data.get("type") == "balance":
        soup = bs(card_data.get("text"), features="lxml")
        balances = map(lambda x: x.find("span").contents[0], soup.find_all("div", {"class": "name"}))
        balances_value = map(lambda x: float(x.find("span").contents[0].strip(" руб.")),
                             soup.find_all("div", {"class": "residue"}))

        res = dict(zip(balances, balances_value))
        cards_data[card] = res
        return res


async def check_cards_balance(q):
    async with aiohttp.ClientSession() as session:
        while True:
            tasks = [
                asyncio.ensure_future(
                    process_card(session, card, q)
                ) for card in cards_data
            ]
            res = await asyncio.gather(*tasks)
            print(res)
            async with aiof.open("cards_data.json", "w") as file:
                await file.write(ujson.dumps(cards_data))
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
