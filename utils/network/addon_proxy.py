import json
import os
import tempfile
from pathlib import Path
from mitmproxy import http
from core.logger_utils import logger, LogIcon


def _resolve_token_file() -> Path:
    """解析捕获 Token 的共享落盘路径，避免强依赖当前工作目录。"""
    try:
        from config import LOG_DIR
        target_dir = LOG_DIR
    except Exception:
        target_dir = Path(tempfile.gettempdir())
    os.makedirs(target_dir, exist_ok=True)
    return target_dir / "temp_token.txt"


# 暂时用不到
class TokenCaptureAddon:

    def response(self, flow: http.HTTPFlow) -> None:
        # 1. 过滤目标接口 (请替换为你 App 真实的登录接口 URL 路径)
        # 例如: https://api.myapp.com/v1/auth/login
        urls = flow.request.pretty_url
        logger.info(f"{LogIcon.FIND} 抓包获取 URL: {urls}")
        if "/userservices/v2/user" in urls and flow.request.method == "POST":
            try:
                # 2. 解析响应体
                response_data = json.loads(flow.response.content)

                # 3. 提取 Token (根据实际 JSON 结构修改)
                # 假设结构: {"code": 200, "data": {"token": "eyJhbG..."}}
                token = response_data.get("data", {}).get("token")

                if token:
                    logger.info(f"{LogIcon.SUCCESS} [Mitmproxy] 成功捕获 Token: {token[:20]}...")

                    # 4. 写入共享文件 (供测试框架读取)
                    token_file = _resolve_token_file()
                    with open(token_file, "w", encoding="utf-8") as f:
                        f.write(token)
            except Exception as e:
                logger.error(f"{LogIcon.FAIL} [Mitmproxy] 解析 Token 失败: {e}")


addons = [TokenCaptureAddon()]



