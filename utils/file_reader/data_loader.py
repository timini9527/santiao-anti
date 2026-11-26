import csv
import re
from pathlib import Path
from typing import Any

import yaml
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from core.logger_utils import logger, LogIcon
import pandas as pd
from config import CONFIG_DIR, DATA_DIR, RESOURCE_DIR


_TEMPLATE_VAR_PATTERN = re.compile(r"\$\{(\w+)\}")


def render_template_data(data: Any, variables: dict[str, Any]) -> Any:
    """
    递归渲染 YAML/JSON 测试数据中的 `${变量名}` 占位符。
    仅替换变量表中显式声明的键，不干扰 SQL 注入、XSS 或普通花括号字符。
    :param data: 待渲染数据（支持 str / list / dict 任意嵌套）
    :param variables: 变量名与替换值映射表
    :return: 渲染后的新数据对象（不修改原始数据）
    """
    if not variables:
        return data
    if isinstance(data, str):
        return _TEMPLATE_VAR_PATTERN.sub(
            lambda m: str(variables[m.group(1)]) if m.group(1) in variables else m.group(0),
            data,
        )
    if isinstance(data, list):
        return [render_template_data(item, variables) for item in data]
    if isinstance(data, dict):
        return {k: render_template_data(v, variables) for k, v in data.items()}
    return data


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
            logger.info(f"{LogIcon.SUCCESS} 快速定位文件成功：{target_path}")
            return target_path
    return None

def load_yaml_data(file_name):
    """
    读取YAML文件并返回数据
    """
    file_path = find_file(file_name)
    if file_path is None:
        logger.error(f"{LogIcon.FAIL} 未找到文件 {file_name}")
        raise FileNotFoundError(f"未找到文件 {file_name}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            # logger.info(f"读取 {file_path} YAML文件 ------ data = {data}")
            # print("读取文件：", data)
        return data
    except yaml.YAMLError as e:
        logger.error(f"{LogIcon.FAIL} YAML解析错误 {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"{LogIcon.FAIL} 文件读取错误 {file_path}: {e}")
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
        logger.error(f"{LogIcon.FAIL} 未找到文件 {file_name}")
        raise FileNotFoundError(f"未找到文件 {file_name}")

    # 3. 回写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        # allow_unicode=True 保证中文不乱码
        # sort_keys=False 保证写入顺序不被打乱
        yaml.dump(auth_data, f, allow_unicode=True, sort_keys=False)

    logger.info(f"{LogIcon.SUCCESS} [Config] Token 已更新至 auth_config.yaml: {auth_token[-15:]}...")


def load_csv_data(file_name):
    """
    读取 CSV 文件并返回数据
    """
    file_path = find_file(file_name)
    if file_path is None:
        logger.error(f"{LogIcon.FAIL} 未找到文件 {file_name}")
        raise FileNotFoundError(f"未找到文件 {file_name}")
    logger.info(f"{LogIcon.FIND} 目标 CSV 文件路径: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            # reader = csv.reader(f)
            data = []
            for row in reader:
                data.append(row)
            # logger.info(f"{LogIcon.FIND} 已读取文件 {data}")
            return data
    except csv.Error as e:
        logger.error(f"{LogIcon.FAIL} CSV 文件解析错误: {e}")
        raise
    except FileNotFoundError:
        logger.error(f"{LogIcon.FAIL} 未找到文件 {file_name}")
        raise
    except Exception as e:
        logger.error(f"{LogIcon.FAIL} 未知错误: {e}")
        raise

def pandas_load_csv_data(file_name):
    """
    pandas 读取 CSV 文件并返回数据
    """
    file_path = find_file(file_name)
    if file_path is None:
        logger.error(f"{LogIcon.FAIL} 未找到文件 {file_name}")
        raise FileNotFoundError(f"未找到文件 {file_name}")
    logger.info(f"{LogIcon.FIND} 目标 CSV 文件路径: {file_path}")

    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')  # 使用 utf-8-sig 自动处理
        data = df.to_dict('records')
        logger.info(f"{LogIcon.FIND} 已读取文件 {data}")
        return data
    except csv.Error as e:
        logger.error(f"{LogIcon.FAIL} CSV 文件解析错误: {e}")
        raise
    except FileNotFoundError:
        logger.error(f"{LogIcon.FAIL} 未找到文件 {file_name}")
        raise
    except Exception as e:
        logger.error(f"{LogIcon.FAIL} 未知错误: {e}")
        raise

def save_csv_data(file_name, data):
    """
    保存数据到 CSV 文件
    """
    file_path = find_file(file_name)
    if file_path is None:
        logger.error(f"{LogIcon.FAIL} 未找到文件 {file_name}")
        raise FileNotFoundError(f"未找到文件 {file_name}")
    logger.info(f"{LogIcon.FIND} 目标文件路径: {file_path}")
    pass



# load_yaml_data('login _data.yaml')
# load_yaml_data('nickname_data.yaml')
# load_yaml_data('email_data.yaml')
# load_yaml_data('api/auth_config.yaml')
# load_yaml_data('devices.yaml')

# load_csv_data('area_data.csv')
# pandas_load_csv_data('area_data.csv')
