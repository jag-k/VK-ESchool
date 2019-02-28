from os.path import join
import configparser
import json

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


# Constants and Types

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
              "   ► Новый номер (перепривязать карту): Вы можете заного привязать карту"
ABOUT_STRING = 'ℹ ️Данный бот создан для отслеживания своего баланса с сервиса ' \
               '"Электронная школа" (http://школа58.рф). Для этого Вам нужно ввести номер своей карты, ' \
               'и в дальнейшем Вам будут приходить уведомления об изменении баланса счёта.\n\n' \
               'Так же, здесь Вы можете проверять свой баланс в любое время суток.'

for i in filter(lambda x: x.lower().endswith("_db"), dir()):
    folder = "database"
    extension = "json"
    exec(f"{i} = '{join(folder, eval(i))}.{extension}'")

if __name__ == '__main__':
    print(SETTINGS)
    print(SECRET)
