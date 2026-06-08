from mitmproxy import http
import json

# 假设登录接口的 URL 包含这个关键词
LOGIN_PATH = "http://192.168.1.148/userservices/v2/user/login"


class TokenInterceptor:
    def response(self, flow: http.HTTPFlow):
        # 过滤出登录接口的响应
        if LOGIN_PATH in flow.request.pretty_url and flow.request.method == "POST":
            try:
                data = json.loads(flow.response.content)
                # 假设 Token 在 response body 的 'data' -> 'access_token' 字段
                # 根据实际接口调整提取逻辑
                token = data.get("data", {}).get("access_token")

                if token:
                    print(f" [Mitmproxy] 捕获到 Token: {token}")
                    # 将 Token 写入共享缓存文件
                    with open(".temp_token_cache", "w") as f:
                        f.write(token)
            except Exception as e:
                print(f" [Mitmproxy] 解析 Token 失败: {e}")


addons = [
    TokenInterceptor()
]
print(" [Mitmproxy] 启动成功")
print(addons)