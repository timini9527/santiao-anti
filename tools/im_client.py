# -*- coding: utf-8 -*-
"""
类微信 IM 客户端（Python 实现）
================================
覆盖内容：
  1. 登录获取 token / 过期自动刷新（TokenManager）
  2. WebSocket 建连时把 token 放进握手请求头（Authorization: Bearer xxx）
     也支持"先连后认证"模式（服务端下发 challenge，首帧回 auth）
  3. 心跳保活（协议层 ping/pong + 应用层 ping 双保险）
  4. 发送消息 + 等待 msg_ack，超时指数退避重发（同一 client_msg_id 幂等）
  5. 单连接滑动窗口限流（asyncio.Semaphore）
  6. 断线自动重连（指数退避 + 随机抖动），重连后按会话 seq 差量同步并补发未 ACK 消息
  7. WS 不可用时 HTTP 兜底发送（POST /api/messages，请求头带 token）

依赖：
    pip install websockets requests

运行示例见文件底部：python im_client.py
"""

import asyncio
import json
import random
import time
import uuid

import requests
import websockets


# ---------------------------------------------------------------------------
# 1. Token 管理
# ---------------------------------------------------------------------------
class TokenManager:
    """
    登录后拿到的 access_token 是同一个凭证，
    同时用于：HTTP 请求头 和 WebSocket 握手请求头。
    """

    def __init__(self, base_url, device_id=None):
        self.base_url = base_url.rstrip("/")
        self.device_id = device_id or uuid.uuid4().hex
        self.access_token = None
        self.refresh_token_ = None
        self.expires_at = 0.0
        self.user_id = None

    def login(self, account, password):
        """Step 1：账号密码登录，拿到业务 token。"""
        resp = requests.post(
            f"{self.base_url}/api/login",
            json={"account": account, "password": password,
                  "device_id": self.device_id},
            timeout=10,
        )
        resp.raise_for_status()
        self._apply(resp.json()["data"])

    def refresh(self):
        """token 过期用 refresh_token 换新。"""
        resp = requests.post(
            f"{self.base_url}/api/token/refresh",
            json={"refresh_token": self.refresh_token_,
                  "device_id": self.device_id},
            timeout=10,
        )
        resp.raise_for_status()
        self._apply(resp.json()["data"])

    def _apply(self, data):
        self.access_token = data["access_token"]
        self.refresh_token_ = data.get("refresh_token")
        self.expires_at = time.time() + int(data.get("expire_in", 7200))
        self.user_id = data.get("user_id")

    def ensure_valid(self):
        """建连 / 发请求前调用：提前 60 秒刷新，避免握手瞬间过期。"""
        if self.access_token is None:
            raise RuntimeError("尚未登录，请先调用 login()")
        if time.time() > self.expires_at - 60:
            self.refresh()

    def http_headers(self):
        """HTTP 通道用的请求头（请求头的 token 就是这里）。"""
        self.ensure_valid()
        return {"Authorization": f"Bearer {self.access_token}"}


# ---------------------------------------------------------------------------
# 2. 待确认消息的内部结构
# ---------------------------------------------------------------------------
class _Pending:
    def __init__(self, frame):
        self.frame = frame
        self.event = asyncio.Event()   # 收到 ACK 时置位
        self.result = None


# ---------------------------------------------------------------------------
# 3. IM 客户端
# ---------------------------------------------------------------------------
class IMClient:
    """
    auth_mode 说明：
      "header"      —— 原生客户端推荐：token 直接放 WS 握手请求头
      "first_frame" —— 通用兜底：先建连，服务端下发 challenge，客户端首帧回 auth 帧
    """

    def __init__(self, ws_url, base_url, token_manager, *,
                 auth_mode="header",
                 max_inflight=100,        # 单连接滑动窗口：最多未确认消息数
                 heartbeat_interval=30.0, # 心跳间隔（秒）
                 ack_timeout=10.0,        # 单条消息等 ACK 的超时
                 max_retries=5,           # WS 重发次数上限
                 on_message=None):
        self.ws_url = ws_url
        self.base_url = base_url.rstrip("/")
        self.token = token_manager
        self.auth_mode = auth_mode
        self.heartbeat_interval = heartbeat_interval
        self.ack_timeout = ack_timeout
        self.max_retries = max_retries
        self.on_message = on_message or (lambda f: None)

        self._ws = None
        self._connected = asyncio.Event()
        self._pending = {}               # client_msg_id -> _Pending
        self._session_seq = {}           # conversation_id -> 本地最大 seq（sync 用）
        self._sem = asyncio.Semaphore(max_inflight)
        self._send_lock = asyncio.Lock() # 串行化底层 send，避免帧交错
        self._last_pong = 0.0
        self._closing = False
        self._runner = None
        self._hb = None

    # ---------------- 生命周期 ----------------
    async def start(self):
        """启动连接协程 + 心跳协程，并等待首次连接成功。"""
        await asyncio.to_thread(self.token.ensure_valid)
        self._runner = asyncio.create_task(self._run_forever())
        self._hb = asyncio.create_task(self._heartbeat_loop())
        await self._connected.wait()

    async def stop(self):
        self._closing = True
        for t in (self._hb, self._runner):
            if t:
                t.cancel()
        if self._ws:
            await self._ws.close()

    # ---------------- 连接与重连 ----------------
    async def _run_forever(self):
        """连接主循环：断开 -> 指数退避 + 随机抖动 -> 重连（防重连风暴）。"""
        backoff = 1.0
        while not self._closing:
            try:
                await self._connect_once()
                backoff = 1.0
                await self._recv_loop()          # 连接关闭时返回
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[IM] 连接异常：{e!r}")
            finally:
                self._connected.clear()
                if self._ws:
                    try:
                        await self._ws.close()
                    except Exception:
                        pass
                    self._ws = None
            if self._closing:
                break
            delay = backoff + random.uniform(0, 1)
            print(f"[IM] {delay:.1f}s 后重连 ...")
            await asyncio.sleep(delay)
            backoff = min(backoff * 2, 30)

    async def _connect_once(self):
        """Step 2：握手建连，token 放请求头；认证通过后进入会话。"""
        await asyncio.to_thread(self.token.ensure_valid)
        headers = {"Authorization": f"Bearer {self.token.access_token}"}
        kwargs = dict(ping_interval=self.heartbeat_interval,
                      ping_timeout=10, max_size=2 ** 20)
        try:
            # websockets >= 12
            self._ws = await websockets.connect(
                self.ws_url, additional_headers=headers, **kwargs)
        except TypeError:
            # websockets < 12 的参数名不同
            self._ws = await websockets.connect(
                self.ws_url, extra_headers=headers, **kwargs)

        if self.auth_mode == "first_frame":
            # 先连后认证：等 challenge -> 首帧回 auth（token 不进 URL/日志）
            challenge = await self._recv_frame(timeout=5)
            if challenge.get("type") != "challenge":
                raise RuntimeError(f"期望 challenge，收到：{challenge}")
            await self._raw_send({
                "type": "auth",
                "token": self.token.access_token,
                "nonce": challenge.get("nonce"),
            })

        # 等服务端 connected 帧（5 秒内）
        deadline = time.time() + 5
        while time.time() < deadline:
            frame = await self._recv_frame(timeout=deadline - time.time())
            if frame.get("type") == "connected":
                break
            await self._handle_frame(frame)
        else:
            raise TimeoutError("等待 connected 帧超时")

        self._last_pong = time.time()
        self._connected.set()

        # 差量同步：带上各会话本地最大 seq，补齐离线期间消息
        await self._raw_send({"type": "sync", "sessions": self._session_seq})

        # 补发断线前仍未收到 ACK 的消息（同 client_msg_id，服务端幂等去重）
        for p in list(self._pending.values()):
            await self._raw_send(p.frame)

    async def _recv_frame(self, timeout):
        raw = await asyncio.wait_for(self._ws.recv(), timeout)
        self._last_pong = time.time()
        return json.loads(raw)

    # ---------------- 接收循环 ----------------
    async def _recv_loop(self):
        async for raw in self._ws:
            self._last_pong = time.time()
            try:
                frame = json.loads(raw)
            except json.JSONDecodeError:
                continue
            await self._handle_frame(frame)

    async def _handle_frame(self, frame):
        ftype = frame.get("type")

        if ftype == "msg_ack":
            p = self._pending.get(frame.get("client_msg_id"))
            if p:
                p.result = frame
                p.event.set()

        elif ftype == "pong":
            self._last_pong = time.time()

        elif ftype in ("msg_push", "msg"):
            self._record_seq(frame)
            self.on_message(frame)

        elif ftype == "sync_result":
            for m in frame.get("messages", []):
                self._record_seq(m)
                self.on_message(m)

        elif ftype in ("auth_fail", "error"):
            print(f"[IM] 服务端错误帧：{frame}")

    def _record_seq(self, frame):
        cid = frame.get("conversation_id")
        seq = frame.get("seq") or frame.get("server_seq")
        if cid and seq is not None:
            self._session_seq[cid] = max(
                self._session_seq.get(cid, 0), int(seq))

    # ---------------- 心跳 ----------------
    async def _heartbeat_loop(self):
        """应用层心跳；协议层 ping/pong 已由 websockets 库自动处理。"""
        while not self._closing:
            await asyncio.sleep(self.heartbeat_interval)
            if self._ws is None:
                continue
            if time.time() - self._last_pong > 2 * self.heartbeat_interval:
                print("[IM] 心跳超时，主动断开触发重连")
                try:
                    await self._ws.close()
                except Exception:
                    pass
                break
            try:
                await self._raw_send({"type": "ping",
                                      "ts": int(time.time() * 1000)})
            except Exception:
                break

    # ---------------- 发送 ----------------
    async def _raw_send(self, frame):
        async with self._send_lock:
            await self._ws.send(json.dumps(frame, ensure_ascii=False))

    async def send_message(self, conversation_id, text, *,
                           http_fallback=True):
        """
        Step 4：发送一条消息并等待 ACK。
        - 先拿滑动窗口信号量（限制未确认消息数，天然限流）
        - 超时未 ACK -> 指数退避重发，client_msg_id 不变（幂等）
        - WS 重发次数用尽 -> HTTP 兜底发送（请求头带 token）
        返回 ACK 帧 dict，失败返回 {"ok": False, ...}
        """
        await self._sem.acquire()
        frame = {
            "type": "msg_send",
            "client_msg_id": uuid.uuid4().hex,
            "conversation_id": conversation_id,
            "content": {"text": text},
            "timestamp": int(time.time() * 1000),
        }
        pending = _Pending(frame)
        self._pending[frame["client_msg_id"]] = pending
        try:
            return await self._send_and_wait(pending, http_fallback)
        finally:
            self._sem.release()
            self._pending.pop(frame["client_msg_id"], None)

    async def _send_and_wait(self, pending, http_fallback):
        backoff = 1.0
        for attempt in range(1, self.max_retries + 1):
            # 断线期间挂起，等重连成功后再继续该条的重发
            await self._connected.wait()
            try:
                await self._raw_send(pending.frame)
            except Exception:
                continue
            try:
                await asyncio.wait_for(pending.event.wait(),
                                       timeout=self.ack_timeout)
                return pending.result          # ACK 成功
            except asyncio.TimeoutError:
                print(f"[IM] 第 {attempt} 次发送未收到 ACK，"
                      f"{backoff:.1f}s 后重发 {pending.frame['client_msg_id'][:8]}")
                await asyncio.sleep(backoff + random.uniform(0, 0.5))
                backoff = min(backoff * 2, 15)

        # WS 通道彻底失败，走 HTTP 兜底
        if http_fallback:
            print("[IM] WS 发送失败，转 HTTP 兜底")
            return await self._http_fallback_send(pending.frame)
        return {"ok": False, "error": "max retries exceeded",
                "client_msg_id": pending.frame["client_msg_id"]}

    async def _http_fallback_send(self, frame):
        def _do():
            resp = requests.post(
                f"{self.base_url}/api/messages",
                json=frame,
                headers=self.token.http_headers(),   # 请求头带 token
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            data.setdefault("client_msg_id", frame["client_msg_id"])
            return data

        try:
            return await asyncio.to_thread(_do)
        except Exception as e:
            return {"ok": False, "error": f"http fallback failed: {e}",
                    "client_msg_id": frame["client_msg_id"]}

    # ---------------- 批量发送（100w 条场景的客户端侧模型） ----------------
    async def send_batch(self, conversation_id, texts, *, http_fallback=True):
        """
        并发发出全部消息，真实并发度由滑动窗口信号量(max_inflight)限制，
        收完一条 ACK 才放行下一条，天然完成限流。
        """
        return await asyncio.gather(*[
            self.send_message(conversation_id, t, http_fallback=http_fallback)
            for t in texts
        ])


# ---------------------------------------------------------------------------
# 4. 使用示例
# ---------------------------------------------------------------------------
if __name__ == "__main__":

    API_BASE = "https://api.example.com"   # ← 换成你的 HTTP 服务地址
    WS_URL = "wss://gw.example.com/ws"     # ← 换成你的 WebSocket 网关地址

    def on_push(frame):
        print("[收到]", frame.get("conversation_id"),
              frame.get("content", {}))

    async def main():
        # Step 1：登录拿 token（此后请求头/握手都用它）
        tm = TokenManager(API_BASE)
        await asyncio.to_thread(tm.login, "your_account", "your_password")

        # Step 2~7：建连（请求头带 token）、心跳、重连、sync 全部自动
        client = IMClient(WS_URL, API_BASE, tm,
                          auth_mode="header",   # 服务端要求首帧认证则改 "first_frame"
                          on_message=on_push)
        await client.start()
        print("[IM] 已连接，可收发消息")

        # Step 4：发单条，等待 ACK
        ack = await client.send_message("cid_1001", "hello im")
        print("[ACK]", ack)

        # 批量示例：同一会话并发 500 条，窗口限流 100
        results = await client.send_batch(
            "cid_1001", [f"batch-{i}" for i in range(500)])
        ok = sum(1 for r in results if r.get("client_msg_id"))
        print(f"[批量] 完成 {ok}/500")

        await asyncio.sleep(3)   # 留出时间接收下行推送
        await client.stop()

    asyncio.run(main())
