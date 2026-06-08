# config.py (位于项目根目录)
from pathlib import Path

# 1. 动态获取项目根目录的绝对路径
# Path(__file__).resolve() 获取当前 config.py 的绝对路径
# .parent 获取它的父目录，也就是项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent

# 2. 定义各个核心资源目录的绝对路径常量
CONFIG_DIR = PROJECT_ROOT / "config"   # 存放框架配置文件
DATA_DIR = PROJECT_ROOT / "data"        # 存放业务测试数据
LOG_DIR = PROJECT_ROOT / "logs"         # 存放日志文件
REPORT_DIR = PROJECT_ROOT / "reports"   # 存放测试报告
SCREENSHOT_DIR = PROJECT_ROOT / "screenshots" # 存放异常截图



