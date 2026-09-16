"""
接口压测业务场景集
包含：鉴权登录、用户信息查询、群聊与消息核心接口的高并发请求封装
"""

import json
from typing import Any, Dict, Optional
from locust.contrib.fasthttp import FastResponse


class ApiScenarios:
    """接口压测用例业务逻辑封装"""

    @staticmethod
    def login_scenario(client: Any, phone: str = "13800000001", code: str = "123456") -> Optional[str]:
        """
        场景 1：用户登录接口压测
        :param client: FastHttpUser 的客户端对象
        :param phone: 手机号
        :param code: 验证码
        :return: 鉴权 Token
        """
        payload: Dict[str, str] = {
            "phone": phone,
            "code": code,
        }
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        
        with client.post(
            "/api/v1/auth/login",
            data=json.dumps(payload),
            headers=headers,
            name="POST /api/v1/auth/login [用户登录]",
            catch_response=True,
        ) as response:
            response: FastResponse
            if response.status_code == 200:
                try:
                    res_data: Dict[str, Any] = response.json()
                    if res_data.get("code") == 0:
                        token: Optional[str] = res_data.get("data", {}).get("token")
                        response.success()
                        return token
                    else:
                        response.failure(f"业务码错误: {res_data.get('msg')}")
                except Exception as e:
                    response.failure(f"JSON解析异常: {str(e)}")
            else:
                response.failure(f"HTTP状态码异常: {response.status_code}")
        return None

    @staticmethod
    def get_user_profile(client: Any, token: str) -> None:
        """
        场景 2：个人信息拉取接口压测（高频只读）
        :param client: FastHttpUser 客户端
        :param token: 用户 Token
        """
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        with client.get(
            "/api/v1/user/profile",
            headers=headers,
            name="GET /api/v1/user/profile [个人资料]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"个人资料获取失败，状态码: {response.status_code}")

    @staticmethod
    def send_chat_message(
        client: Any,
        token: str,
        target_id: str,
        content: str,
        chat_type: str = "single",
    ) -> None:
        """
        场景 3：发送聊天消息接口压测（高并发核心写操作）
        :param client: FastHttpUser 客户端
        :param token: 用户 Token
        :param target_id: 接收者或群ID
        :param content: 消息内容
        :param chat_type: 聊天类型 (single / group)
        """
        payload: Dict[str, Any] = {
            "target_id": target_id,
            "chat_type": chat_type,
            "msg_type": "text",
            "content": content,
        }
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        with client.post(
            "/api/v1/message/send",
            data=json.dumps(payload),
            headers=headers,
            name="POST /api/v1/message/send [发送消息]",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 201):
                try:
                    res_json: Dict[str, Any] = response.json()
                    if res_json.get("code") == 0:
                        response.success()
                    else:
                        response.failure(f"发送消息业务失败: {res_json.get('msg')}")
                except Exception as e:
                    response.failure(f"响应非合法JSON: {str(e)}")
            else:
                response.failure(f"消息接口HTTP错误: {response.status_code}")

    @staticmethod
    def get_conversation_list(client: Any, token: str) -> None:
        """
        场景 4：拉取会话列表（高并发读/轮询场景）
        :param client: FastHttpUser 客户端
        :param token: 用户 Token
        """
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        with client.get(
            "/api/v1/conversation/list",
            headers=headers,
            name="GET /api/v1/conversation/list [会话列表]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"会话列表拉取失败: {response.status_code}")
