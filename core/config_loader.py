import yaml
import os
from core.logger_utils import logger, LogIcon


class ConfigLoader:

    def __init__(self, config_path = f"config/api_config.yaml"):
        # print(f"🚀 加载配置文件: {os.path.dirname(os.path.dirname(__file__))}")
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), config_path)
        self._config  = self.load_yaml_data()


    def load_yaml_data(self):
         """加载 YAML 并根据 current_env 组装最终配置"""
         if not os.path.exists(self.config_path):
             logger.error(f"{LogIcon.FAIL} 配置文件不存在: {self.config_path}")
             raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

         with open(self.config_path, 'r', encoding='utf-8') as f:
             raw_data  = yaml.safe_load(f)

         # 1. 获取当前环境 (优先读取系统环境变量，方便 CI/CD 注入)
         # 如果 Jenkins 设置了 export ENV=prod，则覆盖 yaml 里的 test  获取环境名, 默认为 test
         current_env = os.getenv('ENV', raw_data.get('current_env', 'test'))
         # print(f"🚀 当前环境: {current_env}")

         # 2. 获取公共配置 没有公共配置时，返回空字典
         common_config = raw_data.get('common', {})
         # print(f"🚀 公共配置: {common_config}")

         # 3. 获取特定环境配置 没有特定环境配置时，返回空字典
         env_config = raw_data.get('envs', {}).get(current_env, {})
         # print(f"🚀 特定环境配置: {env_config}")

         # 4. 合并配置 (环境配置 覆盖 公共配置) 重新赋值给 common_config 更新配置
         # 例如：UAT 环境的 timeout 会覆盖或添加 common 里的 timeout
         common_config.update(env_config)

         # 将环境名也存进去，方便日志打印
         common_config['env_name'] = current_env
         # print(f"🚀 最终配置: {common_config}")
         return common_config

    @property
    def data(self):
         """获取最终配置"""
         return self._config


# 单例模式：初始化一次，全局使用
config = ConfigLoader().data

if __name__ == "__main__":
    # 调试打印
    logger.info(f"{LogIcon.SETUP} 当前环境配置: {config['env_name']}")
    logger.info(f"{LogIcon.SETUP} 基础请求地址 Base URL: {config['base_url']}")
    logger.info(f"{LogIcon.SETUP} 全局超时时间 Timeout: {config['timeout']}")



