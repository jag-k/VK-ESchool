# from vk_api.bot_longpoll import VkBotEvent as Event
from config import *
from tinydb import TinyDB, Query
from .auth import Bot
from .helper import *
from balance import sync_get_balance
from vk_api.keyboard import VkKeyboard as Keyboard, VkKeyboardColor as Color


user_state = TinyDB(USER_STATES_DB)
user_card = TinyDB(USER_CARDS_DB)
Query = Query()


def state_handler(status):
    def _(func):
        State(status, func)
        return func
    return _


class State:
    states = {}

    def __init__(self, state_status, func):
        self.states[state_status] = func

    @classmethod
    def use_func(cls, state, bot: Bot):
        def _(state, bot): pass
        return cls.states.get(state, _)(cls, bot)

    @staticmethod
    def set_state(state, bot: Bot):
        user_id = bot.from_id
        user = {
            "user_id": user_id,
            "state": state
        }
        return user_state.upsert(user, Query.user_id == user_id)

    @staticmethod
    def get_state(bot: Bot):
        return user_state.get(Query.user_id == bot.from_id)


def message_handler(bot: Bot):
    user_id = bot.from_id
    user = user_state.get(Query.user_id == user_id)
    if not user:
        user = {
            "user_id": user_id,
            "state": 0
        }
        user_state.insert(user)

    print(f"https://vk.com/id{bot.from_id} ({State.get_state(bot).get('state')}): {bot.text}")
    return State.use_func(user.get("state"), bot)


# KEYBOARDS

MAIN_KB = Keyboard()
MAIN_KB.add_button("Баланс", Color.POSITIVE)
MAIN_KB.add_button("Перепривязать карту", Color.DEFAULT)
MAIN_KB.add_line()
MAIN_KB.add_button("Справка", Color.PRIMARY)
MAIN_KB.add_button("О приложении", Color.PRIMARY)
MAIN_KB.add_line()
MAIN_KB.add_button("Отписаться", Color.NEGATIVE)

HELP_ONLY_KB = Keyboard()
HELP_ONLY_KB.add_button("Справка", Color.PRIMARY)

BOOL_KB = Keyboard(True)
BOOL_KB.add_button("Да", Color.NEGATIVE)
BOOL_KB.add_button("Нет", Color.POSITIVE)

START_KB = Keyboard(True)
START_KB.add_button("Начать", Color.PRIMARY, {"command": "start"})


# STATES

@state_handler(0)
def start(state: State, bot: Bot):
    print("State:", state.get_state(bot))

    bot.send_forward("Здравствуйте!) Для начала введите номер карты в формате **-******, где * это цифры\n\n"
                     "Например: 39-212345", keyboard=HELP_ONLY_KB)
    state.set_state(1, bot)


@state_handler(1)
def get_card_number(state: State, bot: Bot):

    user_id = bot.from_id
    error_msg = "⚠ ️Данные карты не верны! Попроьбуйте ввести номер карты снова.\n\n"\
                "Подсказка: номер карты в формате **-******, где * это цифры\n"\
                "Например: 39-212345"
    text = remove_from_string(strip(bot.text.strip(), '"', '"'), '-', "_", " ")
    if text.isdigit() and len(text) == 8:
        text = text[0:2] + '-' + text[2:]

        res = sync_get_balance(text)  # type: dict
        if res and not res.get("type") == "error":
            msg = to_balance_string(res)

            with TinyDB(CARDS_DB) as db:
                db.upsert(res, Query.card == res.get('card'))

            user_card.upsert({"user_id": user_id, "card": res.get('card')}, Query.user_id == user_id)
            state.set_state(2, bot)
            bot.send_forward(msg, kb=MAIN_KB)
            return

    elif text.lower() in ("о приложении", "о программе", "о боте", "about", "что это такое",
                          "для чего", "для чего это", "для чего это нужно", "?", "справка", "помощь"):
        bot.send_forward(ABOUT_STRING, keyboard=HELP_ONLY_KB)
        return
    bot.send_forward(error_msg, keyboard=HELP_ONLY_KB)


@state_handler(2)
def main_branch(state: State, bot: Bot):

    text = strip(bot.text.strip(), '!', '/').lower()
    if text in ('balance', 'баланс', ',fkfyc'):
        try:
            bot.send_forward(
                to_balance_string(sync_get_balance(user_card.get(Query.user_id == bot.from_id).get("card"))),
                kb=MAIN_KB
            )
        except Exception as err:
            bot.send_forward(USER_SERVER_ERROR_STRING)
            raise err

    elif text in ("привязать новую карту", "перепривязать карту", "новая карта", "новый номер", "привязать новый номер",
                  "перепривязать номер"):
        bot.send_forward("Введите номер карты в формате **-******, где * это цифры\n\n"
                         "Например: 39-212345", kb=HELP_ONLY_KB)
        state.set_state(1, bot)

    elif text in ("cancel", "break", "unsubscribe", "отмена", "отписка", "удалить", "отписаться"):
        bot.send_forward("Вы точно хотите отписаться от рассылки и удалить данные о своей карте у бота?",
                         kb=BOOL_KB)
        state.set_state(3, bot)

    elif text in ("gjvjon", "help", "?", "h", "помощь", "справка"):
        bot.send_forward(HELP_STRING, kb=MAIN_KB)

    elif strip(text, "?", '.', "!") in ("о приложении", "о программе", "о боте", "about", "что это такое",
                                        "для чего", "для чего это", "для чего это нужно"):
        bot.send_forward(ABOUT_STRING, kb=MAIN_KB)

    else:
        bot.send_forward("⚠️ Такой комманды не существует! "
                         "Повторите снова или напишите \"помощь\" для получения справки.",
                         kb=MAIN_KB)


@state_handler(3)
def unsubscribe(state: State, bot: Bot):  # TODO: Сделать отписку
    text = bot.text.lower().strip()
    user_id = bot.from_id
    if text in ("да", "yes", "y", "д"):
        with TinyDB(CARDS_DB) as db:
            for i in db:
                card = i.get("card")
                if user_card.count(Query.card == card) == 1:

                    db.remove(doc_ids=[i.doc_id])
        user_card.remove(Query.user_id == user_id)
        user_state.remove(Query.user_id == user_id)

        bot.send_forward("Вы успешно удалены из базы данных! Для начала работы, напишите что-нибудь", kb=START_KB)
    else:
        bot.send_forward("Вы отменили отписку."
                         "\n\n💵 Для проверки баланса, напишите \"баланс\".\n"
                         "📃 Для дополнительной информации, отправьте \"помощь\"",
                         kb=MAIN_KB)
        state.set_state(2, bot)
