from core.logger_utils import logger
from utils.file_reader.data_loader import load_yaml_data
from apis.base_api import BaseApi




class CollectionApi:

    def __init__(self):
        self.auth_config = load_yaml_data('auth_config.yaml')['headers']
        self.open_id = self.auth_config['open_id']

    def get_all_collection_data(self):
        """ 获取所有收藏数据 """
        if not self.open_id:
            raise ValueError("未获取到 open_id，请检查 auth_config.yaml 是否包含该字段")

        url = f'/collectapi/v1/users/{self.open_id}/collects/'
        try:
            res = BaseApi().request("GET", url)
            assert res.status_code == 200, f"获取所有收藏数据请求失败，状态码: {res.status_code}"
            res_json = res.json()
            logger.info(f"获取所有收藏数据成功: {res_json}")
            print(f"获取所有收藏数据成功: {res_json}")
            return res_json
        except Exception as e:
            logger.error(f"获取所有收藏数据请求失败: {e}")
            print(f"获取所有收藏数据请求失败: {e}")
            raise e


