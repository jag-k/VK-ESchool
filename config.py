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

for i in filter(lambda x: x.lower().endswith("_db"), dir()):
    folder = "database"
    extension = "json"
    exec(f"{i} = '{join(folder, eval(i))}.{extension}'")

if __name__ == '__main__':
    print(SETTINGS)
    print(SECRET)
