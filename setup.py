import os
import sys

import vk_api

PATH = "data/.secret"

FILE = "secret.ini"

PATTERN = """[vk_data]
login=%s
password=%s
group_id=%s"""
flag = True
while flag:
    login = input("Введите логин: ")
    pwd = input("Введите пароль: ")

    try:
        session = vk_api.VkApi(login, pwd)
        session.auth()

        api = session.get_api()
        flag = False

    except Exception as err:
        print("ОШИБКА! Вы ввели не верные данные, повторите ввод", file=sys.stderr)

else:
    group_id = input("Введите ID группы: ")
    while True:
        try:
            res = api.groups.getById(group_id=group_id, fields="is_admin")[0]
            if res["is_admin"]:
                print(f'Бот привязан у группе "{res["name"]}" (https://vk.com/{res["screen_name"]})')
                break
            print(f'Вы не являетесь администратором группы "{res["name"]}", введите ID другой группы',
                  file=sys.stderr)

        except Exception as err:
            print(f"ОШИБКА ({type(err).__name__})! Повторите снова", file=sys.stderr)

        group_id = input("Введите ID группы: ")

if not os.path.isdir(PATH):
    os.mkdir(PATH)

with open(os.path.join(PATH, FILE), 'w') as file:
    file.write(PATTERN % (login, pwd, group_id))
