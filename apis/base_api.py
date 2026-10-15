import  allure
import requests

from core.logger_utils import logger, LogIcon
from core.config_loader import config
from utils.file_reader.data_loader import load_yaml_data


# HTTP 协议基类
class BaseApi:
    # 从配置文件读取 HOST
    BASE_UTL = config["base_url"]
    TIMEOUT = config["timeout"]
    VERIFY = config["verify"]

    # 设置全局 Token
    data = load_yaml_data('api/auth_config.yaml')["headers"]

    if data.get('Authorization') and data.get('open_id'):
        config["headers"]["Authorization"] = data.get('Authorization')
        config["headers"]["open_id"] = data.get('open_id')

    HEADERS = config["headers"]

    def __init__(self, session =  None):
        # 复用 Session，实现 Cookie/Token 自动携带
        self.session = session if session else requests.Session()
        self.session.headers.update(self.HEADERS)

    @classmethod
    def set_token(cls, token):
        """设置全局 Token"""
        # cls.HEADERS["Authorization"] = f"Bearer {token}"
        cls.HEADERS["Authorization"] = f"{token}"

    # 发送请求
    @allure.step("HTTP Request")
    def request(self, method, url, **kwargs):
        url = f'{self.BASE_UTL}{url}'

        # 如果调用时没传 timeout，使用全局配置的 timeout
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.TIMEOUT

        # 如果调用时没传 verify，使用全局配置
        # if "verify" not in kwargs:
        kwargs["verify"] = self.VERIFY

        # 统一处理 Headers (如 Token)
        if "headers" not in kwargs:
            kwargs["headers"] = self.HEADERS
            # kwargs["headers"] = {}

        # kwargs["headers"]["Authorization"] = f"Bearer {self.token}"

        logger.info(f"{LogIcon.FIND} 发送 HTTP 请求: {method} {url} | 请求体: {kwargs.get('json', '')}")

        try:
            response = requests.request(method, url, **kwargs)
            logger.info(f"{LogIcon.SUCCESS} 收到 HTTP 响应: 状态码 {response.status_code} | 响应体: {response.text[:200]}...")  # 截断日志防止过长

            # 将请求详情附加到 Allure
            allure.attach(url, "Request URL", allure.attachment_type.TEXT)
            allure.attach(response.text, "Response Body", allure.attachment_type.JSON)
            return  response
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} HTTP 请求执行失败: {e}")
            raise e

