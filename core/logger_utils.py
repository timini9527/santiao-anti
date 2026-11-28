# 统一日志处理
import os
import sys
import time
import logging
from logging.handlers import TimedRotatingFileHandler
import colorlog
from colorlog.escape_codes import parse_colors

# 确保在 Windows 控制台环境下输出 UTF-8，彻底杜绝 GBK 导致的 UnicodeEncodeError 与 emoji 转义
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _resolve_log_path() -> str:
    """解析可写日志目录，优先复用根目录 config.LOG_DIR，无写权限时回退至用户目录。"""
    candidates: list[str] = []
    try:
        from config import LOG_DIR
        candidates.append(str(LOG_DIR))
    except Exception:
        pass

    default_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    if default_dir not in candidates:
        candidates.append(default_dir)
    candidates.append(os.path.join(os.path.expanduser("~"), "SantiaoAutoTest", "logs"))

    for cand in candidates:
        try:
            os.makedirs(cand, exist_ok=True)
            probe = os.path.join(cand, ".log_write_probe")
            with open(probe, "w", encoding="utf-8") as f:
                f.write("ok")
            os.remove(probe)
            return cand
        except Exception:
            continue

    return candidates[-1]


# 日志保存路径（自动兼容只读安装卷与多级目录创建）
LOG_PATH: str = _resolve_log_path()


# 是否在控制台输出日志 (False=隐藏, True=显示)
ENABLE_CONSOLE_LOG = True
# 是否启用 Emoji 图标（False 则自动降级为 [ACTION]、[SUCCESS] 等纯文本标签，兼容无 UTF-8 的 CI 终端）
ENABLE_LOG_ICONS = os.getenv("ENABLE_LOG_ICONS", "true").lower() in ("true", "1", "yes")


class LogIcon:
    """系统统一日志语义图标（强类型收口）"""
    ACTION  = "🚀"   # 动作操作: 点击、输入、滑动、页面跳转等主动操作
    FIND    = "🔍"   # 查找识别: 查找元素、提取文本、遍历列表容器、OCR匹配
    WAIT    = "⏳"   # 等待轮询: 显式等待、状态轮询、加载耗时监测
    SUCCESS = "✅"   # 成功就绪: 操作完成、断言通过、状态确认就绪
    WARN    = "⚠️"   # 警告容错: 元素重试、非致命降级、偶发 Toast 捕获
    FAIL    = "❌"   # 失败阻断: 断言失败、异常熔断、超时报错
    SETUP   = "🧪"   # 测试数据: 前置造数据、环境重置、策略建造者
    STEP    = "📌"   # 测试步骤: 用例步骤、阶段锚点
    CAMERA  = "📸"   # 截图留证: 异常截图、报告归档

    # 纯文本降级映射表
    FALLBACK_MAP = {
        ACTION: "[ACTION]",
        FIND: "[FIND]",
        WAIT: "[WAIT]",
        SUCCESS: "[SUCCESS]",
        WARN: "[WARN]",
        FAIL: "[FAIL]",
        SETUP: "[SETUP]",
        STEP: "[STEP]",
        CAMERA: "[CAMERA]",
    }

    # 历史与非标图标归一化映射表（自动纠偏并统一为系统标准 LogIcon）
    NORMALIZE_MAP = {
        # 查找识别类归一 -> FIND (🔍)
        "🔎": FIND,
        "🎯": FIND,
        "📊": FIND,
        "📋": FIND,
        # 主动动作类归一 -> ACTION (🚀)
        "🖱️": ACTION,
        "👉": ACTION,
        "✍️": ACTION,
        "⌨️": ACTION,
        "🔙": ACTION,
        "🔄": ACTION,
        "📱": ACTION,
        "🎹": ACTION,
        "⚡": ACTION,
        "🎴": ACTION,
        "📜": ACTION,
        "📝": ACTION,
        # 等待轮询类归一 -> WAIT (⏳)
        "⌛": WAIT,
        "⏱️": WAIT,
        # 成功就绪类归一 -> SUCCESS (✅)
        "✔️": SUCCESS,
        "🎉": SUCCESS,
        "🏁": SUCCESS,
        # 警告容错类归一 -> WARN (⚠️)
        "🔔": WARN,
        # 失败阻断类归一 -> FAIL (❌)
        "✖️": FAIL,
        "💥": FAIL,
        "🚫": FAIL,
        "🛑": FAIL,
        # 截图留证类归一 -> CAMERA (📸)
        "📷": CAMERA,
        # 测试数据/环境类归一 -> SETUP (🧪)
        "🛠️": SETUP,
        "⚙️": SETUP,
        "📂": SETUP,
        "🌐": SETUP,
        "🧹": SETUP,
        # 测试步骤/阶段类归一 -> STEP (📌)
        "⏭️": STEP,
        "⏩": STEP,
    }


def normalize_log_message(msg: str) -> str:
    """规范化日志消息中的语义图标与间距，自动纠偏历史非标写法并支持无 Emoji 纯文本降级"""
    if not isinstance(msg, str):
        return msg

    # 1. 自动对历史非标图标纠偏归一化为标准 LogIcon
    for legacy_icon, std_icon in LogIcon.NORMALIZE_MAP.items():
        if legacy_icon in msg:
            msg = msg.replace(legacy_icon, std_icon)

    # 2. 针对常见无图标前缀自动补全语义图标（如纯手写 '[Action]'、'[Wait]'、'[Verify]' 等）
    if msg.startswith(("[Action", "[Click", "[Input", "[Scroll")):
        msg = f"{LogIcon.ACTION} {msg}"
    elif msg.startswith(("[Wait", "[Timeout")):
        msg = f"{LogIcon.WAIT} {msg}"
    elif msg.startswith(("[Verify", "[Assert", "[Check", "[Compare", "[Signature")):
        msg = f"{LogIcon.FIND} {msg}"
    elif msg.startswith(("[Setup", "[Clean", "[Teardown")):
        msg = f"{LogIcon.SETUP} {msg}"

    # 3. 清理冗余的内联历史前缀标签（如 "🚀[Action-chat] - chat " -> "🚀 "，避免与元数据重复）
    import re
    msg = re.sub(
        r'([🚀🔍⏳✅⚠️❌🧪📌📸])\s*\[(?:Action|Wait|Verify|Assert|Check|Setup|Teardown|Clean|Error|Fail)[^\]]*\](?:\s*-\s*[^\s]+)?\s*',
        r'\1 ',
        msg
    )

    # 4. 若全局关闭了图标输出，则自动转为纯文本标签
    if not ENABLE_LOG_ICONS:
        for icon, tag in LogIcon.FALLBACK_MAP.items():
            if icon in msg:
                msg = msg.replace(icon, tag)
        return msg

    # 5. 规范化间距：确保图标与后续非空字符之间有且仅有一个半角空格，保持控制台与文件严格对齐
    all_icons = (
        LogIcon.ACTION, LogIcon.FIND, LogIcon.WAIT,
        LogIcon.SUCCESS, LogIcon.WARN, LogIcon.FAIL,
        LogIcon.SETUP, LogIcon.STEP, LogIcon.CAMERA
    )
    for icon in all_icons:
        if icon in msg:
            # 图标紧贴字符时自动插入空格，如 "✅成功" -> "✅ 成功"
            msg = re.sub(rf'{re.escape(icon)}(?=[^\s])', f'{icon} ', msg)
            # 图标后有多个连续空格时压缩为一个空格，如 "✅  成功" -> "✅ 成功"
            msg = re.sub(rf'{re.escape(icon)}\s{{2,}}', f'{icon} ', msg)
    return msg


class AdvancedFormatter(logging.Formatter):
    """高级文件日志格式化器（添加统一的对齐图标，无 ANSI 颜色 escape 码）"""
    LEVEL_ICONS = {
        'DEBUG': '🔵 ',
        'INFO': '🟢 ',
        'WARNING': '🟡 ',
        'ERROR': '🔴 ',
        'CRITICAL': '🟥 ',
    }
    LEVEL_TEXTS = {
        'DEBUG': '[DEBUG]',
        'INFO': '[INFO]',
        'WARNING': '[WARN]',
        'ERROR': '[ERROR]',
        'CRITICAL': '[CRIT]',
    }

    def format(self, record):
        orig_levelname = record.levelname
        orig_msg = record.msg
        if ENABLE_LOG_ICONS:
            record.levelname = self.LEVEL_ICONS.get(orig_levelname, orig_levelname)
        else:
            record.levelname = self.LEVEL_TEXTS.get(orig_levelname, orig_levelname)
        record.msg = normalize_log_message(str(record.msg))
        result = super().format(record)
        record.levelname = orig_levelname
        record.msg = orig_msg
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
    LEVEL_TEXTS = {
        'DEBUG': '[DEBUG]',
        'INFO': '[INFO]',
        'WARNING': '[WARN]',
        'ERROR': '[ERROR]',
        'CRITICAL': '[CRIT]',
    }

    def format(self, record):
        orig_levelname = record.levelname
        orig_msg = record.msg
        line_color = parse_colors(self.log_colors.get(orig_levelname, ""))
        if ENABLE_LOG_ICONS:
            record.levelname = self.LEVEL_ICONS.get(orig_levelname, orig_levelname)
        else:
            record.levelname = self.LEVEL_TEXTS.get(orig_levelname, orig_levelname)
        record.msg = normalize_log_message(str(record.msg))
        result = super().format(record)
        # 部分终端会在换行时丢失 ANSI 状态，因此每个物理行都重新应用当前日志级别颜色。
        if line_color and "\n" in result:
            result = result.replace("\n", f"\n{line_color}")
        record.levelname = orig_levelname
        record.msg = orig_msg
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
        self._bind_semantic_methods()

    def _bind_semantic_methods(self):
        """为全局 logger 对象动态注入语义化快捷输出方法（强类型图标自动集成，支持精准 caller 溯源）"""
        lg = self.logger
        if not hasattr(lg, 'action'):
            lg.action = lambda msg, *args, **kwargs: lg.info(f"{LogIcon.ACTION} {msg}", *args, stacklevel=kwargs.pop("stacklevel", 2), **kwargs)
        if not hasattr(lg, 'find'):
            lg.find = lambda msg, *args, **kwargs: lg.info(f"{LogIcon.FIND} {msg}", *args, stacklevel=kwargs.pop("stacklevel", 2), **kwargs)
        if not hasattr(lg, 'wait'):
            lg.wait = lambda msg, *args, **kwargs: lg.info(f"{LogIcon.WAIT} {msg}", *args, stacklevel=kwargs.pop("stacklevel", 2), **kwargs)
        if not hasattr(lg, 'success'):
            lg.success = lambda msg, *args, **kwargs: lg.info(f"{LogIcon.SUCCESS} {msg}", *args, stacklevel=kwargs.pop("stacklevel", 2), **kwargs)
        # 显式覆盖 warn，规避 Python 3.13 原生 Logger.warn 废弃警告并注入 LogIcon.WARN 图标
        lg.warn = lambda msg, *args, **kwargs: lg.warning(f"{LogIcon.WARN} {msg}", *args, stacklevel=kwargs.pop("stacklevel", 2), **kwargs)
        if not hasattr(lg, 'fail'):
            lg.fail = lambda msg, *args, **kwargs: lg.error(f"{LogIcon.FAIL} {msg}", *args, stacklevel=kwargs.pop("stacklevel", 2), **kwargs)
        if not hasattr(lg, 'setup'):
            lg.setup = lambda msg, *args, **kwargs: lg.info(f"{LogIcon.SETUP} {msg}", *args, stacklevel=kwargs.pop("stacklevel", 2), **kwargs)
        if not hasattr(lg, 'step'):
            lg.step = lambda msg, *args, **kwargs: lg.info(f"{LogIcon.STEP} {msg}", *args, stacklevel=kwargs.pop("stacklevel", 2), **kwargs)
        if not hasattr(lg, 'camera'):
            lg.camera = lambda msg, *args, **kwargs: lg.info(f"{LogIcon.CAMERA} {msg}", *args, stacklevel=kwargs.pop("stacklevel", 2), **kwargs)

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
            # --- Handler: 控制台输出 (绑定 sys.stdout 确保顺序一致并兼容 Windows UTF-8) ---
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)

            # 控制台输出格式：整行渲染相同的日志等级颜色，并通过行首空格规避 [ 被吞，reset=True 保证末尾自动换行复位
            color_fmt = ' %(log_color)s[%(asctime)s.%(msecs)03d] | %(levelname)s | %(filename)-22s:%(lineno)-4d (%(funcName)-20s) ❯ %(message)s '
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
                    '[DEBUG]': 'light_cyan',
                    '[INFO]': 'green',
                    '[WARN]': 'yellow',
                    '[ERROR]': 'red',
                    '[CRIT]': 'bold_red',
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


