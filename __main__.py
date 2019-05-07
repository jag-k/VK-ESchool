from queue import Empty
from typing import Iterator

from vk_api.bot_longpoll import VkBotLongPoll, VkBotEvent
from vk_api.bot_longpoll import VkBotEventType as et
from vk_api.exceptions import ApiError

from modules.auth import api, session, user_id, group_id, Bot
from modules.handler import message_handler, TinyDB, Query
from config import *
from balance import BALANCE_UPDATE

from requests.exceptions import ReadTimeout

longpoll = VkBotLongPoll(session, group_id, wait=25)
thread = Thread("bot")


# Functions

def listen(q: Queue) -> Iterator[VkBotEvent]:
    try:
        while q.run:
            try:
                event = q.get_nowait()
                print("\x1b[34mTHREADING EVENT: %s\x1b[0m" % event)
                if event:
                    if type(event) == dict:
                        yield event
                    else:
                        yield from event
            except Empty:
                pass
            yield from longpoll.check()
    except ReadTimeout:
        yield from listen(q)


@thread.add_thread("Bot Thread")
def bot_thread(q: Queue):
    print("\x1b[32;1mBot Started\x1b[0m")
    logging.info("Bot Started")
    try:
        Bot.send_msg(message="Бот запущен", user_id=user_id)
    except ApiError as err:
        if err.code == 15:
            print(
                "У Вашего приложения нет доступа к отправке сообщений. Подробнее тут: https://vk.com/dev/messages_api",
                file=sys.stderr
            )
            logging.error(
                "У Вашего приложения нет доступа к отправке сообщений. Подробнее тут: https://vk.com/dev/messages_api"
            )
            thread.stop()
            sys.exit(0)

    try:
        for event in listen(q):
            try:
                if type(event) == dict:  # BALANCE EVENT
                    if event.get("type") == BALANCE_UPDATE or False:
                        print("\x1b[32mBALANCE UPDATE: %s\x1b[0m" % event)
                        print("Event", event)
                        msg = "💰 ИЗМЕНЕНИЕ БАЛАНСА: \n" +\
                              '\n'.join(map(lambda x: "  ► %s: " % x +
                                                      "%s₽ (%s₽)" % (
                                                          event.get('new_balance', {}).get('balance', {}).get(x, 0),
                                                          event['change'][x]
                                                      ),
                                            event['change'])) +\
                            '\n\n💵 Для проверки баланса, напишите "баланс".\n' \
                            '📃 Для дополнительной информации, отправьте "помощь"'

                        with TinyDB(USER_CARDS_DB) as db:
                            for user in db.search(Query.card == event['card']):
                                Bot.send_msg(msg, user_id=user['user_id'])

                elif event.type == et.MESSAGE_NEW:
                    message_handler(Bot(event))
            except BaseException as err:
                print('\n')
                traceback.print_exc()
                error_msg = "ERROR (%s): %s" % (type(err).__name__, err)
                logging.error(error_msg)
                Bot.send_msg(message=error_msg, user_id=user_id)

    except ConnectionError:
        print("CONNECTION ERROR", file=sys.stderr)
        logging.error("CONNECTION ERROR")

    except KeyboardInterrupt or SystemExit:
        print("System Exit")
        logging.warning("System Exit")

    except BaseException as err:
        print("%s: %s" % (type(err).__name__, err))
        logging.error("%s: %s" % (type(err).__name__, err))
        raise err

    finally:
        Bot.send_msg(message="Бот остановлен (финальная отправка в лс)", user_id=user_id)
        print("Bot Stopped", file=sys.stderr)
        logging.warning("Bot Stopped")


def main():
    thread.run()


if __name__ == '__main__':
    main()
