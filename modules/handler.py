from vk_api.bot_longpoll import VkBotEvent as Event
from config import *
from tinydb import TinyDB, Query

user_state = TinyDB(DB_NAME).table("user_state")
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
    def use_func(cls, state, event: Event, bot):
        def _(event, state, bot): pass
        return cls.states.get(state, _)(event, cls, bot)

    @staticmethod
    def set_state(state, event: Event):
        id = event.from_id
        user = {
            "user_id": id,
            "state": state
        }
        return user_state.upsert(user, Query.user_id == id)

    @staticmethod
    def get_state(event: Event):
        return user_state.get(Query.user_id == event.from_id)


def message_handler(event: Event, bot):
    id = event.from_id
    user = user_state.get(Query.user_id == id)
    if not user:
        user = {
            "user_id": id,
            "state": 0
        }
        user_state.insert(user)

    return State.use_func(user.get("state"), event, bot)


@state_handler(0)
def start(event: Event, state: State, bot):
    pass
