import vk_api
from config import vk_data
from vk_api.bot_longpoll import VkBotEvent

try:
    session = vk_api.VkApi(vk_data["login"], vk_data["password"], api_version="5.89")
    session.auth()
    group_id = vk_data["group_id"]

    api = session.get_api()  # type: vk_api.vk_api.VkApiMethod
except Exception as err:
    print(err)
    from setup import api, session, group_id


class Bot:
    def __init__(self, event: VkBotEvent):
        if "api" not in dir(self):
            raise AttributeError("Bot has no API. Use Bot.init_bot(api, group_id) before use bot class")
        self.event = event
        print(dict(event))

    @classmethod
    def send_msg(cls, message, domain=None, user_id=None, user_ids=None, peer_id=None, chat_id=None, **kwargs):
        return api.messages.send(
            message=message,
            group_id=group_id,
            domain=domain,
            user_id=user_id,
            user_ids=user_ids,
            peer_id=peer_id,
            chat_id=chat_id,
            **kwargs
        )

    def send_forward(self, message, **kwargs):
        return self.send_msg(message, peer_id=self.msg.peer_id, **kwargs)


user_id = session.token.get("user_id")
if __name__ == '__main__':
    print("USER ID:", user_id)
    print(session.token)
