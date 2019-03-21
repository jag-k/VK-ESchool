import os
import sys

import vk_api

PATH = os.path.join(os.curdir, "data", ".secret")

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
    groups = api.groups.get(extended=True, filter="admin")
    print("У Вас есть %s сообществ, которые Вы можете использовать:" % groups.get('count'))
    print(*map(lambda x: 'Сообщество "%s" (http://vk.com/%s):\n' % (x.get("name"), x.get("screen_name")) +
                         '    ID: ' + str(x.get("id")), groups.get("items")), sep="\n\n")

    group_id = input("Введите ID группы: ")
    while True:
        try:
            res = api.groups.getById(group_id=group_id, fields="is_admin")[0]
            if res["is_admin"]:
                print('Бот привязан у группе "%s" (https://vk.com/%s)' % (res['name'], res['screen_name']))
                group_id = res["id"]
                break
            print('Вы не являетесь администратором группы "%s", введите ID другой группы' % {res["name"]},
                  file=sys.stderr)

        except Exception as err:
            print("ОШИБКА (%s)! Повторите снова" % type(err).__name__, file=sys.stderr)

        group_id = input("Введите ID группы: ")

if not os.path.isdir(PATH):
    os.mkdir(PATH)

with open(os.path.join(PATH, FILE), 'w', encoding="utf-8") as file:
    file.write(PATTERN % (login, pwd, group_id))
