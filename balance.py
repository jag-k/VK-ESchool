import asyncio
import ujson
from queue import Empty
from sys import stderr

import aiohttp
from bs4 import BeautifulSoup as bs
from requests import post

from tinydb import TinyDB, Query
from aiotinydb import AIOTinyDB
from config import *

thread = Thread("bot")


# Functions

def expense_change(old, new):
    res = {}
    old, new = old['balance'], new['balance']
    for n in new:
        res[n] = float(new[n]) - float(old.get(n, 0))

    for o in old:
        if o not in res:
            res[o] = float(new.get(o, 0)) - float(old[o])
    return res


def sync_get_balance(card):
    req = post("http://xn--58-6kc3bfr2e.xn--p1ai/ajax/",
                        data={"card": card, "act": "FreeCheckBalance"},
                        headers={
                            "Content-Type": "application/x-www-form-urlencoded"
                        })
    if req.status_code == 200:
        result = req.json()
        if result.get('type', "error") == "error":
            print("Card %s not found" % card, file=stderr)

        if result and result.get("type") == "balance":
            soup = bs(result.get("text"), features="lxml")
            balances = map(lambda x: x.find("span").contents[0], soup.find_all("div", {"class": "name"}))
            balances_value = map(lambda x: float(x.find("span").contents[0].strip(" руб.")),
                                 soup.find_all("div", {"class": "residue"}))

            return {"card": card, "balance": dict(zip(balances, balances_value))}
        return result


async def get_balance(session, card):
    logging.debug("\x1b[33mSearch %s\x1b[0m" % card)
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
                        print("Card %s not found" % card, file=stderr)

                    if result and result.get("type") == "balance":
                        soup = bs(result.get("text"), features="lxml")
                        balances = map(lambda x: x.find("span").contents[0], soup.find_all("div", {"class": "name"}))
                        balances_value = map(lambda x: float(x.find("span").contents[0].strip(" руб.")),
                                             soup.find_all("div", {"class": "residue"}))

                        return {"card": card, "balance": dict(zip(balances, balances_value))}
                    return result

                except ValueError:
                    print("Card %s is not JSON" % card, file=stderr)
                    return {}
    except aiohttp.ClientConnectionError:
        print("Card %s connection error" % card, file=stderr)
        return {}


async def process_card(session, card, cards_data, q):
    try:
        event = q.get_nowait()
        print("EVENT IN THREAD", event)
        if type(event) == SystemExit:
            sys.exit(0)
    except Empty:
        pass

    res = await get_balance(session, card)  # type: dict
    if res and not res.get("type") == "error":
        old_balance = list(filter(lambda x: x.get("card") == card, cards_data))[0]
        logging.debug(old_balance)
        if res["balance"] != old_balance['balance']:
            q.put_nowait({
                "type": BALANCE_UPDATE,
                "new_balance": res,
                "old_balance": old_balance,
                "change": expense_change(old_balance, res),
                "card": card,
            })

        async with AIOTinyDB(CARDS_DB) as db:
            db.upsert(res, Query().card == card)
        return res


async def check_cards_balance(q):
    async with aiohttp.ClientSession() as session:
        while q.run:
            async with AIOTinyDB(CARDS_DB) as db:
                dat = db.all()

            tasks = [
                asyncio.ensure_future(
                    process_card(session, card['card'], dat, q)
                ) for card in dat
            ]
            res = await asyncio.gather(*tasks)
            logging.debug(res)

            if not q.run:
                break
            await asyncio.sleep(SLEEP_TIME)


@thread.add_thread("Balance Thread")
def balanced_thread(q: Queue):
    ioloop = asyncio.new_event_loop()
    ioloop.run_until_complete(check_cards_balance(q))
    ioloop.close()


def main():
    thread.run()


if __name__ == '__main__':
    main()
