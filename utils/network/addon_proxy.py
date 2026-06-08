import  json
from mitmproxy import http


# 暂时用不到
class TokenCaptureAddon :

    def response(self, flow: http.HTTPFlow):
        # 1. 过滤目标接口 (请替换为你 App 真实的登录接口 URL 路径)
        # 例如: https://api.myapp.com/v1/auth/login
        urls = flow.request.pretty_url
        print(f" 获取所有 :    {urls}  ")
        if "/userservices/v2/user" in urls and flow.request.method == "POST":
            try:
                # 2. 解析响应体
                response_data = json.loads(flow.response.content)

                # 3. 提取 Token (根据实际 JSON 结构修改)
                # 假设结构: {"code": 200, "data": {"token": "eyJhbG..."}}
                token = response_data.get("data", {}).get("token")

                if token:
                    print(f"✅ [Mitmproxy] 成功捕获 Token: {token[:20]}...")

                    # 4. 写入共享文件 (供测试框架读取)
                    with open("temp_token.txt", "w", encoding="utf-8") as f:
                        f.write(token)
            except Exception as e:
                print(f"❌ [Mitmproxy] 解析 Token 失败: {e}")


addons = [TokenCaptureAddon()]



