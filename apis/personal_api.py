from urllib.parse import urlparse
from apis.base_api import BaseApi
from core.logger_utils import logger
from utils.file_reader.data_loader import load_yaml_data



class PersonalAPI:
    def __init__(self):
        # 1. 改为在初始化时加载配置，确保拿到的是登录后的最新 Token/OpenID
        super().__init__()  # 如果 BaseApi 有初始化逻辑，记得调用
        self.auth_config = load_yaml_data('auth_config.yaml')['headers']
        self.open_id = self.auth_config['open_id']

    def get_personal_info(self):
        """ 获取个人信息  """
        if not self.open_id:
            raise ValueError("未获取到 open_id，请检查 auth_config.yaml 是否包含该字段")

        url = f'/userservices/v2/users/{self.open_id}'
        try:
            res = BaseApi().request("GET", url)
            assert res.status_code == 200, f"获取个人信息请求失败，状态码: {res.status_code}"
            # 3. 打印请求详情 (最重要的一步)
            # print("\n======== DEBUG INFO ========")
            # print(f"URL: {res.request.url}")
            # print(f"Headers: {res.request.headers}")
            # print(f"Body: {res.request.body}")  # GET 请求通常为 None
            # print(f"Response: {res.text}")
            # print("============================\n")
            res_json = res.json()
            return res_json
        except Exception as e:
            logger.error(f"获取个人信息请求失败: {e}")
            print(f"获取个人信息请求失败: {e}")
            raise e

    def get_avatar_info(self):
        """ 获取用户头像 """
        if not self.open_id:
            raise ValueError("OpenID 为空")

        url = (f'/imageapi/v1/namespaces/public/avatar/personal/{self.open_id}')
        try:
            # allow_redirects=False 禁止重定向，手动处理
            res = BaseApi().request("GET", url, allow_redirects=False)
            # 兼容 301 和 302
            assert res.status_code in [301, 302], f"预期重定向，实际状态码: {res.status_code}"

            redirect_url = res.headers['Location']
            if not redirect_url:
                raise ValueError("响应头中未找到 Location 字段")

            logger.info(f"获取到重定向地址: {redirect_url}")

            # 3. 【核心改进】使用标准库解析 URL，不再依赖 IP 中的 '20/'
            # 假设 URL 是 http://121.204.228.20/11,0ac50358bff236?width=...
            # urlparse(url).path 会得到 "/11,0ac50358bff236"
            parsed_path = urlparse(redirect_url).path

            avatar_id = parsed_path.lstrip('/')  # 去掉开头的 '/'
            if not avatar_id:
                raise ValueError(f"解析头像 ID 失败，Path 为: {parsed_path}")

            # print(parsed_path)
            # print(avatar_id)
            logger.info(f"解析头像 ID 成功: {avatar_id}")
            return avatar_id
        except Exception as e:
            logger.error(f"获取用户头像请求失败: {e}")
            print(f"获取用户头像请求失败: {e}")
            raise e


# PersonalAPI().get_personal_info()
# PersonalAPI().get_avatar_info()





