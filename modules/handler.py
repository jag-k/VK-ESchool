# from vk_api.bot_longpoll import VkBotEvent as Event
from config import *
from tinydb import TinyDB, Query
from .auth import Bot
from .helper import *
from balance import sync_get_balance

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
        id = bot.from_id
        user = {
            "user_id": id,
            "state": state
        }
        return user_state.upsert(user, Query.user_id == id)

    @staticmethod
    def get_state(bot: Bot):
        return user_state.get(Query.user_id == bot.from_id)


def message_handler(bot: Bot):
    id = bot.from_id
    user = user_state.get(Query.user_id == id)
    if not user:
        user = {
            "user_id": id,
            "state": 0
        }
        user_state.insert(user)

    print(f"https://vk.com/id{bot.from_id} ({State.get_state(bot).get('state')}): {bot.text}")
    return State.use_func(user.get("state"), bot)


# STATES

@state_handler(0)
def start(state: State, bot: Bot):
    print("State:", state.get_state(bot))
    bot.send_forward("Здравствуйте!) Для начала введите номер карты в формате **-******, где * это цифры\n\n"
                     "Например: 39-212345")
    state.set_state(1, bot)


@state_handler(1)
def get_card_number(state: State, bot: Bot):
    user_id = bot.from_id
    error_msg = "⚠️Данные карты не верны! Попроьбуйте ввести номер карты снова.\n\n"\
                "Подсказка: номер карты в формате **-******, где * это цифры\n"\
                "Например: 39-212345"
    text = remove_from_string(strip(bot.text.strip(), '"', '"'), '-', "_", " ")
    if text.isdigit() and len(text) == 8:
        text = text[0:2] + '-' + text[2:]
        print("CArd:", text)

        res = sync_get_balance(text)  # type: dict
        if res and not res.get("type") == "error":
            print("OK")
            msg = to_balance_string(res)

            with TinyDB(CARDS_DB) as db:
                db.upsert(res, Query.card == res.get('card'))

            user_card.upsert({"user_id": user_id, "card": res.get('card')}, Query.user_id == user_id)
            state.set_state(2, bot)
            bot.send_forward(msg)
            return

    elif text.lower() in ("о приложении", "о боте", "помощь", "?", "справка"):
        bot.send_forward('ℹ️Данный бот создан для отслеживания своего баланса с сервиса '
                         '"Электронная школа" (http://школа58.рф). Для этого Вам нужно ввести номер своей карты, '
                         'и в дальнейшем Вам будут приходить уведомления об изменении баланса счёта.\n\n'
                         'Так же, здесь Вы можете проверять свой баланс в любое время суток.')
        return
    bot.send_forward(error_msg)


@state_handler(2)
def main_branch(state: State, bot: Bot):
    text = strip(bot.text.strip(), '!', '/').lower()
    if text in ('balance', 'баланс', ',fkfyc'):
        try:
            bot.send_forward(
                to_balance_string(sync_get_balance(user_card.get(Query.user_id == bot.from_id).get("card")))
            )
        except Exception as err:
            bot.send_forward(USER_SERVER_ERROR_STRING)
            raise err
    elif text in ("gjvjon", "help", "?", "h", "помощь", "справка"):
        bot.send_forward("Ну тут должен быть HELP_STRING, но значит [id173996641|КТО-ТО] это не доделал")
        # TODO: Сделать HELP_STRING
    else:
        bot.send_forward("⚠️ Такой комманды не существует! "
                         "Повторите снова или напишите \"помощь\" для получения справки.")
