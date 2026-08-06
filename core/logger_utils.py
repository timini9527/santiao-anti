# 统一日志处理
import os
import time
import logging
from logging.handlers import TimedRotatingFileHandler
import colorlog
from colorlog.escape_codes import parse_colors


# 日志保存路径
# LOG_PATH = os.path.join(os.getcwd(), "logs")
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
# print("LOG_PATH: ", LOG_PATH)
if not os.path.exists(LOG_PATH):
    os.mkdir(LOG_PATH)


# 是否在控制台输出日志 (False=隐藏, True=显示)
ENABLE_CONSOLE_LOG = True
# ENABLE_CONSOLE_LOG = False


class AdvancedFormatter(logging.Formatter):
    """高级文件日志格式化器（添加统一的对齐图标，无 ANSI 颜色 escape 码）"""
    LEVEL_ICONS = {
        'DEBUG': '🔵 ',
        'INFO': '🟢 ',
        'WARNING': '🟡 ',
        'ERROR': '🔴 ',
        'CRITICAL': '🟥 ',
    }

    def format(self, record):
        orig_levelname = record.levelname
        record.levelname = self.LEVEL_ICONS.get(orig_levelname, orig_levelname)
        result = super().format(record)
        record.levelname = orig_levelname
        return result


class AdvancedColoredFormatter(colorlog.ColoredFormatter):
    """高级控制台日志格式化器（带对齐图标，且支持单独对元数据着色，保持正文清晰）"""
    LEVEL_ICONS = {
        'DEBUG': '🔵 ',
        'INFO': '🟢 ',
        'WARNING': '🟡 ',
        'ERROR': '🔴 ',
        'CRITICAL': '🟥 ',
    }

    def format(self, record):
        orig_levelname = record.levelname
        line_color = parse_colors(self.log_colors.get(orig_levelname, ""))
        record.levelname = self.LEVEL_ICONS.get(orig_levelname, orig_levelname)
        result = super().format(record)
        # 部分终端会在换行时丢失 ANSI 状态，因此每个物理行都重新应用当前日志级别颜色。
        if line_color and "\n" in result:
            result = result.replace("\n", f"\n{line_color}")
        record.levelname = orig_levelname
        return result


class LoggerUtils:
    """
    日志工具类：封装并定制高级的 logging 输出
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
        # 1. 定义文件日志输出格式（包含毫秒精确度，用特殊的管道符号分隔，结构极度清晰）
        # 格式：[时间] [级别] [文件名:行号] - 信息
        # 确保格式字符串完全正确，不要漏掉 's' 或 'd'
        # %(asctime)s     -> 时间字符串
        # %(levelname)s   -> 级别字符串
        # %(filename)s    -> 文件名字符串
        # %(lineno)d      -> 行号整数 (注意是 d)
        # %(funcName)s     -> 函数名字符串
        # %(message)s     -> 消息内容
        log_fmt_str = '[%(asctime)s.%(msecs)03d] | %(levelname)s | %(filename)-22s:%(lineno)-4d (%(funcName)-20s) ❯ %(message)s'
        date_fmt_str = '%Y-%m-%d %H:%M:%S'
        formatter = AdvancedFormatter(log_fmt_str, datefmt=date_fmt_str)

        # 获取当前日期，用于文件名
        date_time = time.strftime('%Y-%m-%d')

        # 创建 File Handler
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

            # 2. 控制台输出格式：整行渲染相同的日志等级颜色（INFO 全绿，DEBUG 全青蓝），通过行首空格规避 [ 被吞的 Bug，并启用 reset=True 保证末尾自动换行复位
            color_fmt = ' %(log_color)s[%(asctime)s.%(msecs)03d] | %(levelname)s| %(filename)-22s:%(lineno)-4d (%(funcName)-20s) ❯ %(message)s'
            color_formatter = AdvancedColoredFormatter(
                color_fmt,
                datefmt=date_fmt_str,
                reset=True,
                log_colors={
                    'DEBUG': 'light_cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'bold_red',
                    '🔵 ': 'light_cyan', # 匹配 DEBUG
                    '🟢 ': 'green',      # 匹配 INFO
                    '🟡 ': 'yellow',     # 匹配 WARNING
                    '🔴 ': 'red',        # 匹配 ERROR
                    '🟥 ': 'bold_red',   # 匹配 CRITICAL
                }
            )
            console_handler.setFormatter(color_formatter)
            self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger

logger = LoggerUtils().get_logger()

# logger.debug("debug")
# logger.info("info")
# logger.warning("warning")
# logger.error("error")
# logger.critical("critical")


