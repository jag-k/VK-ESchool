import configparser
import logging
import os
import sys
import threading
import time
import traceback
from os.path import join
from queue import Queue


if not os.path.isdir('logs'):
    os.mkdir('logs')

logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]:  %(message)s',
                    level=logging.DEBUG, filename="logs/" + time.asctime() + '.log')

settings = configparser.ConfigParser()
settings.read("./data/settings.ini")

SETTINGS = {}
for key in settings:
    SETTINGS[key] = dict(settings[key])


secret = configparser.ConfigParser()
secret.read("./data/.secret/secret.ini")

SECRET = {}
for key in secret:
    SECRET[key] = dict(secret[key])

vk_data = SECRET.get('vk_data')


class Thread:
    groups = {}
    STOP_PROGRAM = SystemExit("program stop")

    def __init__(self, group=None):
        if group in self.groups:
            t = self.groups[group]
            self.threads = t.threads
            self.q = t.q
            self.working_thread = t.working_thread
        else:
            self.groups[group] = self
            self.threads = []
            self.q = Queue()
            self.q.run = False
            self.working_thread = []

    def add_thread(self, name: str = None, args: list = None):
        def _(func):
            self.threads.append({"name": name, "args": args or [], "func": func})

            def err_catcher(*args, **kwargs):
                try:
                    func(*args, **kwargs)
                except Exception as err:
                    print("Thread err:", err)
                    if type(err) not in (SystemExit, KeyboardInterrupt):
                        traceback.print_exc()
                        self.stop()
            return err_catcher
        return _

    def stop(self):
        self.q.put(self.STOP_PROGRAM)
        self.q.run = False
        sys.exit(1)

    def run(self):
        self.working_thread = [threading.Thread(target=t['func'], name=t['name'],
                                                args=tuple([self.q] + list(t['args'])))
                               for t in self.threads]

        self.q.run = True
        for t in self.working_thread:
            t.start()

        self.q.join()


# Constants and Types

DEBUG = True

SLEEP_TIME = 30
CARDS_DB = "cards_data"
USER_STATES_DB = "user_states_data"
USER_CARDS_DB = "user_cards_data"

BALANCE_UPDATE = "bl"

USER_SERVER_ERROR_STRING = "Тут какая-то ошибка на сервере случилась.. Попробуйте снова попзже)"
HELP_STRING = "ℹ ️У Бота есть несколько комманд:\n" \
              "   ► Помощь (справка): Выводит данное сообщение\n" \
              "   ► Баланс: Позволяет узнать баланс ващего счёта\n" \
              "   ► О боте (о программе): Выводит справку о том, для чего этот бот нужен\n" \
              "   ► Новый номер (перепривязать карту): Вы можете заново привязать карту"
ABOUT_STRING = 'ℹ ️Данный бот создан для отслеживания своего баланса с сервиса ' \
               '"Электронная школа" (http://школа58.рф). Для этого Вам нужно ввести номер своей карты, ' \
               'и в дальнейшем Вам будут приходить уведомления об изменении баланса счёта.\n\n' \
               'Так же, здесь Вы можете проверять свой баланс в любое время суток.'


folder = "database"
extension = "json"
if not os.path.isdir(folder):
    os.mkdir(folder)

for i in filter(lambda x: x.lower().endswith("_db"), dir()):
    exec("%s = '%s.%s'" % (i, join(folder, eval(i)), extension))

if __name__ == '__main__':
    print(SETTINGS)
    print(SECRET)
