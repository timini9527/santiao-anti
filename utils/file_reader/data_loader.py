import csv
from pathlib import Path
from typing import Any

import yaml
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from core.logger_utils import logger
import pandas as pd
from config import CONFIG_DIR, DATA_DIR, RESOURCE_DIR


def find_file(filename: str) -> Any | None:
    """
    最佳实践：在指定的核心资源目录中精确查找文件，告别全盘扫描
    """
    if '..' in filename or filename.startswith('/') or '/.' in filename:
        raise ValueError("Invalid filename: potential path traversal detected")

    # 【核心逻辑】：定义需要搜索的优先级目录列表,它会先找 configs 目录，再去 data 目录找
    search_dirs = [CONFIG_DIR, DATA_DIR, RESOURCE_DIR]

    for directory in search_dirs:
        # 使用 / 符号拼接路径
        target_path = directory / filename

        # 判断该绝对路径下的文件是否存在
        if target_path.exists() and target_path.is_file():
            logger.info(f"✅ 快速定位文件成功：{target_path}")
            return target_path
    return None

def load_yaml_data(file_name):
    """
    读取YAML文件并返回数据
    """
    file_path = find_file(file_name)
    if file_path is None:
        logger.error(f"未找到文件 {file_name}")
        raise FileNotFoundError(f"未找到文件 {file_name}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            # logger.info(f"读取 {file_path} YAML文件 ------ data = {data}")
            # print("读取文件：", data)
        return data
    except yaml.YAMLError as e:
        logger.error(f"YAML解析错误 {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"文件读取错误 {file_path}: {e}")
        raise


def update_token(token, open_id):
    """
    更新 Token 到 auth_config.yaml
    """
    file_name = 'api_config.yaml'
    # 1. 先读取现有内容
    data = load_yaml_data(file_name)

    # 2. 修改内存中的值
    # 结构是 common -> headers -> Authorization
    if "common" not in data:
        data["common"] = {}
    if "headers" not in data["common"]:
        data["common"]["headers"] = {}

    # 注意：通常 Token 需要加 Bearer 前缀，根据你具体项目调整
    auth_token = f"{token}"
    data['common']['headers']['Authorization'] = auth_token
    data['common']['headers']['open_id'] = open_id
    auth_data = data['common']
    # print("data: ", data)

    file_path = find_file('auth_config.yaml')
    if file_path is None:
        logger.error(f"未找到文件 {file_name}")
        raise FileNotFoundError(f"未找到文件 {file_name}")

    # 3. 回写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        # allow_unicode=True 保证中文不乱码
        # sort_keys=False 保证写入顺序不被打乱
        yaml.dump(auth_data, f, allow_unicode=True, sort_keys=False)

    print(f" [Config] Token 已更新至 auth_config.yaml: {auth_token[-15:]}...")


def load_csv_data(file_name):
    """
    读取 CSV 文件并返回数据
    """
    file_path = find_file(file_name)
    if file_path is None:
        logger.error(f"未找到文件 {file_name}")
        raise FileNotFoundError(f"未找到文件 {file_name}")
    print("file_path: ", file_path)

    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            # reader = csv.reader(f)
            data = []
            for row in reader:
                data.append(row)
            logger.info(f"已读取文件 {data}")
            print("data_list: ", data)
            return data
    except csv.Error as e:
        logger.error(f"CSV 文件解析错误: {e}")
        raise
    except FileNotFoundError:
        logger.error(f"未找到文件 {file_name}")
        raise
    except Exception as e:
        logger.error(f"未知错误: {e}")
        raise

def pandas_load_csv_data(file_name):
    """
    pandas 读取 CSV 文件并返回数据
    """
    file_path = find_file(file_name)
    if file_path is None:
        logger.error(f"未找到文件 {file_name}")
        raise FileNotFoundError(f"未找到文件 {file_name}")
    print("file_path: ", file_path)

    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')  # 使用 utf-8-sig 自动处理
        data = df.to_dict('records')
        logger.info(f"已读取文件 {data}")
        print("data_list: ", data)
        return data
    except csv.Error as e:
        logger.error(f"CSV 文件解析错误: {e}")
        raise
    except FileNotFoundError:
        logger.error(f"未找到文件 {file_name}")
        raise
    except Exception as e:
        logger.error(f"未知错误: {e}")
        raise

def save_csv_data(file_name, data):
    """
    保存数据到 CSV 文件
    """
    file_path = find_file(file_name)
    if file_path is None:
        logger.error(f"未找到文件 {file_name}")
        raise FileNotFoundError(f"未找到文件 {file_name}")
    print("file_path: ", file_path)
    pass



# load_yaml_data('login _data.yaml')
# load_yaml_data('nickname_data.yaml')
# load_yaml_data('email_data.yaml')
# load_yaml_data('api/auth_config.yaml')
# load_yaml_data('devices.yaml')

# load_csv_data('area_data.csv')
# pandas_load_csv_data('area_data.csv')
