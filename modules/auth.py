import vk_api
from config import vk_data

try:
    session = vk_api.VkApi(vk_data["login"], vk_data["password"], api_version="5.89")
    session.auth()
    group_id = vk_data["group_id"]

    api = session.get_api()  # type: vk_api.vk_api.VkApiMethod
except Exception as err:
    print(err)
    from setup import api, session, group_id

user_id = session.token.get("user_id")
if __name__ == '__main__':
    print("USER ID:", user_id)
    print(session.token)
