import sys
import traceback
import threading
from queue import Queue, Empty
from typing import Iterator

from vk_api.bot_longpoll import VkBotLongPoll, VkBotEvent
from vk_api.bot_longpoll import VkBotEventType as et

from modules.auth import api, session, user_id, group_id, Bot
from modules.handler import message_handler
from balance import balanced_thread, get_balance, BALANCE_UPDATE

longpoll = VkBotLongPoll(session, group_id, wait=1)


# Functions

def listen(q: Queue) -> Iterator[VkBotEvent]:
    while True:
        try:
            event = q.get_nowait()
            print(f"\x1b[34mTHREADING EVENT: {event}\x1b[0m")
            if event:
                if type(event) == dict:
                    yield event
                else:
                    yield from event
        except Empty:
            pass
        yield from longpoll.check()


def bot_thread(q: Queue):
    print("Bot Started")
    Bot.send_msg(message="Бот запущен", user_id=user_id)

    try:
        for event in listen(q):
            try:
                if type(event) == dict:  # BALANCE EVENT
                    if event.get("type") == BALANCE_UPDATE or False:
                        print(f"\x1b[32mBALANCE UPDATE: {event}\x1b[0m")

                elif event.type == et.MESSAGE_NEW:
                    message_handler(Bot(event))
            except BaseException as err:
                print('\n')
                traceback.print_exc()
                error_msg = "ERROR (%s): %s" % (type(err).__name__, err)
                Bot.send_msg(message=error_msg, user_id=user_id)

    except ConnectionError:
        print("CONNECTION ERROR", file=sys.stderr)

    except KeyboardInterrupt or SystemExit:
        print("System Exit")

    finally:
        send_msg(message="Бот остановлен (финальная отправка в лс)", user_id=user_id)
        print("Bot Stopped", file=sys.stderr)


def main():
    q = Queue()
    balance = threading.Thread(target=balanced_thread, args=(q, ))
    bot = threading.Thread(target=bot_thread, args=(q, ))
    balance.start()
    bot.start()

    q.join()


if __name__ == '__main__':
    main()
