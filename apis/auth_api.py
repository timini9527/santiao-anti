from core.logger_utils import logger, LogIcon
from utils.file_reader.data_loader import  load_yaml_data, update_token
from apis.base_api import BaseApi

class AuthApi(BaseApi):

    def login(self):
        """ 调用接口登录，并持久化 Token """
        url = '/userservices/v2/user/login'
        data = load_yaml_data('accounts.yaml')['test_account'][1]
        # print("data: ", data)
        payload = {
            "username": data['username'],
            "password": data['password'],
            "verify_type": data['verify_type'],
            "verify_value": data['verify_value'],
            "device_type": data['device_type'],
            "device_id": data['device_id'],
            "device": data['device']
        }
        # print("payload: ", payload)
        try:
            res = self.request("POST", url, json=payload)
            assert res.status_code == 200, f"登录失败，状态码: {res.status_code}"

            # 解析 Token，假设结构是 res.json()['data']['token']
            res_json = res.json()
            token = res_json['token']
            open_id = res_json['open_id']

            if token:
                # 更新 Token 到 auth_config.yaml
                update_token(token, open_id)
                return token
            else:
                logger.error(f"{LogIcon.FAIL} 登录响应中未找到 Token")
                # print("登录响应中未找到 Token")
                raise ValueError("登录响应中未找到 Token")
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} 登录失败: {e}")
            raise e


# AuthApi().login()



