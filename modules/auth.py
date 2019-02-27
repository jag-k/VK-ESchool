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
        self.event = event
        self.msg = event.object

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

    def __getattr__(self, item):
        return self.msg.__getattr__(item)


user_id = session.token.get("user_id")
if __name__ == '__main__':
    print("USER ID:", user_id)
    print(session.token)
