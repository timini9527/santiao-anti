# 统一日志处理
import os
import time
import logging
from logging.handlers import TimedRotatingFileHandler
import colorlog


# 日志保存路径
# LOG_PATH = os.path.join(os.getcwd(), "logs")
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
# print("LOG_PATH: ", LOG_PATH)
if not os.path.exists(LOG_PATH):
    os.mkdir(LOG_PATH)


# 是否在控制台输出日志 (False=隐藏, True=显示)
ENABLE_CONSOLE_LOG = True
# ENABLE_CONSOLE_LOG = False


class LoggerUtils:
    """
    日志工具类：封装 logging 模块
    """
    def __init__(self, logger_name="AutoTest"):
        self.logger = logging.getLogger(logger_name)
        # 1. 全局 logger 级别调低到 DEBUG，保证最底层的拦截不发生
        self.logger.setLevel(logging.DEBUG)

        # 核心判断：如果 logger 已经有处理器了，就不要再添加了
        # 这能解决 "日志重复打印" 的问题
        if not self.logger.handlers:
            self.initialize_handlers()

    def initialize_handlers(self):
        # 1. 定义日志输出格式
        # 格式：[时间] [级别] [文件名:行号] - 信息
        # 确保格式字符串完全正确，不要漏掉 's' 或 'd'
        # %(asctime)s     -> 时间字符串
        # %(levelname)s   -> 级别字符串
        # %(filename)s    -> 文件名字符串
        # %(lineno)d      -> 行号整数 (注意是 d)
        # %(funcName)s     -> 函数名字符串
        # %(message)s     -> 消息内容
        log_fmt_str = '[%(asctime)s] - [%(levelname)-7s] - [%(filename)-22s:%(lineno)-4d] - [%(funcName)-20s] - %(message)s'
        formatter = logging.Formatter(log_fmt_str)

        # 获取当前日期，用于文件名
        date_time = time.strftime('%Y-%m-%d')

        # === 封装一个内部方法来创建 Handler，避免代码重复 ===
        def create_file_handler(filename_suffix, level):
            """
            :param filename_suffix: 文件名后缀，如 'error.log'
            :param level: 日志等级，如 logging.ERROR
            """
            file_path = os.path.join(LOG_PATH, f"{date_time}_{filename_suffix}")

            # 使用时间滚动切割 (每天午夜生成新文件，保留1天)
            handler = TimedRotatingFileHandler(
                filename=file_path,
                when="MIDNIGHT",
                interval=1,
                backupCount=1,
                encoding="utf-8"
            )
            handler.setLevel(level)
            handler.setFormatter(formatter)
            return handler

        # === 3. 创建4个不同的日志文件 Handler ===
        # (1) Error Log: 仅记录 ERROR 和 CRITICAL
        f_error = create_file_handler('error.log', logging.ERROR)

        # (2) Warning Log: 记录 WARNING, ERROR, CRITICAL
        f_warning = create_file_handler('warning.log', logging.WARNING)

        # (3) Info Log: 记录 INFO 及以上 (通常是主要查看的文件)
        f_info = create_file_handler('info.log', logging.INFO)

        # (4) All Log: 记录所有，修改为 DEBUG 以记录最全的日志
        f_all = create_file_handler('all.log', logging.DEBUG)

        # === 4. 将处理器添加到 logger ===
        self.logger.addHandler(f_error)
        self.logger.addHandler(f_warning)
        self.logger.addHandler(f_info)
        self.logger.addHandler(f_all)

        if ENABLE_CONSOLE_LOG:
            # # --- Handler 3: 控制台输出 ---
            console_handler = logging.StreamHandler()
            # 2. 控制台输出级别调低到 DEBUG
            console_handler.setLevel(logging.DEBUG)

            # 定义颜色格式
            color_fmt = '%(log_color)s[%(asctime)s] [%(levelname)-7s] [%(filename)-22s:%(lineno)-4d] [%(funcName)-20s] - %(message)s'
            color_formatter = colorlog.ColoredFormatter(
                color_fmt,
                log_colors={
                    'DEBUG': 'bold_cyan',
                    'INFO': 'bold_green',
                    'WARNING': 'bold_yellow',
                    'ERROR': 'bold_red',
                    'CRITICAL': 'bold_white',
                }
            )
            console_handler.setFormatter(color_formatter)
            self.logger.addHandler(console_handler)


    def get_logger(self):
        return self.logger

logger = LoggerUtils().get_logger()

