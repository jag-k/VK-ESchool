def strip(string: str, *args) -> str:
    old = None
    while old != string:
        old = string
        for i in args:
            string = string.strip(i)
    return string


def split(string: str, *args) -> list:
    _, *args = args
    string = string.split(_)
    for i in args:
        string = [j for s in string for j in s.split(i)]
    return string


def remove_from_string(string: str, *args) -> str:
    for i in args:
        string = ''.join(string.split(i))
    return string


def to_balance_string(data):
    return f"💳 Ваш номер карты: {data.get('card')}\n" \
               f"💰 Текущий баланс по счетам:\n\n" + \
           '\n'.join(
               map(lambda b:
                   f"   ► {b}: {data['balance'][b]}",
                   data.get("balance", {}))) + \
           "\n\n💵 Для проверки баланса, напишите \"баланс\".\n"\
           "📃 Для дополнительной информации, отправьте \"помощь\""
