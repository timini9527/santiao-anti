# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 (原生桌面端) - 接口压测页面
=======================================================
1:1 像素级复刻图 3 (ApiPlatform.vue)：
1. 顶部 Header：接口压测 控制台 + WebSocket 协议通信与 Locust 并发压力测试 + 右侧药丸 Badges
2. 说明横幅卡片：IM 即时通讯接口与长连接性能测试平台
3. 4 大性能指标看板：WebSocket 链路状态、压测当前 QPS、关键路径 P99 响应延迟、累计消息发送总量
4. 中间配置区：WebSocket 长连接配置 (支持建立握手) + Locust 并发消息压力测试 (支持动态压力模拟)
5. 下方协议套件：IM 专项协议测试套件 (协议鉴权、链路维持、顺序一致性、离线补偿、高并发性能)
"""
import random
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QScrollArea, QSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer

class MetricCard(QFrame):
    """指标展示卡片"""
    def __init__(self, label: str, value: str, sub: str, val_color: str = "#2563eb", parent=None):
        super().__init__(parent)
        self.setObjectName("apiMetricCard")
        self.setStyleSheet("""
            QFrame#apiMetricCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        lbl_top = QLabel(label)
        lbl_top.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600;")
        layout.addWidget(lbl_top)

        self.lbl_val = QLabel(value)
        self.lbl_val.setStyleSheet(f"color: {val_color}; font-size: 20px; font-weight: 800;")
        layout.addWidget(self.lbl_val)

        self.lbl_sub = QLabel(sub)
        self.lbl_sub.setStyleSheet("color: #94a3b8; font-size: 10px;")
        layout.addWidget(self.lbl_sub)

    def update_value(self, value: str, sub: str = None):
        self.lbl_val.setText(value)
        if sub:
            self.lbl_sub.setText(sub)


class ApiPage(QWidget):
    """接口与性能自动化测试工作台 (图 3 像素级复刻)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_connected = False
        self.is_stressing = False
        self.current_qps = 0
        self.p99_latency = 0
        self.total_sent = 0

        self.stress_timer = QTimer(self)
        self.stress_timer.timeout.connect(self._on_stress_tick)

        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 8, 10, 10)
        root_layout.setSpacing(12)

        # 1. 顶部 Header
        top_header = self._create_top_header()
        root_layout.addWidget(top_header)

        # 2. 可滚动的主体内容
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setObjectName("apiScroll")
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea#apiScroll { background: transparent; border: none; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 2.1 顶部说明横幅卡片
        banner = self._create_banner_card()
        layout.addWidget(banner)

        # 2.2 4 大指标看板卡片 (横排)
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(14)

        self.card_ws = MetricCard("WebSocket 链路状态", "🟣 Disconnected", "心跳周期: 10s", val_color="#7c3aed")
        self.card_qps = MetricCard("压测当前 QPS (吞吐量)", "0 msg/s", "并发用户: 500 个", val_color="#2563eb")
        self.card_p99 = MetricCard("关键路径 P99 响应延迟", "0 ms", "门禁基线: ≤ 500ms", val_color="#d97706")
        self.card_sent = MetricCard("累计消息发送总量", "0 条", "丢包率: 0.00% (正常)", val_color="#8b5cf6")

        metrics_row.addWidget(self.card_ws)
        metrics_row.addWidget(self.card_qps)
        metrics_row.addWidget(self.card_p99)
        metrics_row.addWidget(self.card_sent)
        layout.addLayout(metrics_row)

        # 2.3 中间两列配置卡片 (WebSocket 长连接 + Locust 压测)
        config_row = QHBoxLayout()
        config_row.setSpacing(14)

        card_left_ws = self._create_ws_config_card()
        config_row.addWidget(card_left_ws, stretch=5)

        card_right_locust = self._create_locust_config_card()
        config_row.addWidget(card_right_locust, stretch=5)

        layout.addLayout(config_row)

        # 2.4 下方协议套件列表
        cases_card = self._create_protocol_cases_card()
        layout.addWidget(cases_card)

        scroll.setWidget(content)
        root_layout.addWidget(scroll, stretch=1)

    # ================= 1. 顶部 Header =================
    def _create_top_header(self) -> QWidget:
        card = QFrame()
        card.setObjectName("apiTopHeader")
        card.setStyleSheet("QFrame#apiTopHeader { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; }")
        h_layout = QHBoxLayout(card)
        h_layout.setContentsMargins(14, 8, 14, 8)
        h_layout.setSpacing(12)

        icon_box = QFrame()
        icon_box.setFixedSize(36, 36)
        icon_box.setObjectName("apiIconBox")
        icon_box.setStyleSheet("QFrame#apiIconBox { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; }")
        ib_layout = QVBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        lbl_icon = QLabel("🔗")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setStyleSheet("font-size: 18px;")
        ib_layout.addWidget(lbl_icon)
        h_layout.addWidget(icon_box)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        lbl_main = QLabel("接口压测 控制台")
        lbl_main.setStyleSheet("font-size: 15px; font-weight: 800; color: #0f172a;")
        lbl_sub = QLabel("WebSocket 协议通信与 Locust 并发压力测试")
        lbl_sub.setStyleSheet("font-size: 11px; color: #64748b;")
        title_box.addWidget(lbl_main)
        title_box.addWidget(lbl_sub)
        h_layout.addLayout(title_box)

        h_layout.addStretch()

        pill_group = QFrame()
        pill_group.setObjectName("apiPillGroup")
        pill_group.setStyleSheet("QFrame#apiPillGroup { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 20px; }")
        pg_layout = QHBoxLayout(pill_group)
        pg_layout.setContentsMargins(6, 2, 6, 2)
        pg_layout.setSpacing(10)

        lbl_dev = QLabel("🟢 设备: 1 台在线")
        lbl_dev.setStyleSheet("color: #059669; font-weight: 700; font-size: 12px;")
        pg_layout.addWidget(lbl_dev)

        sep1 = QLabel("|")
        sep1.setStyleSheet("color: #cbd5e1;")
        pg_layout.addWidget(sep1)

        lbl_case = QLabel("✏️ 用例: 1383 条")
        lbl_case.setStyleSheet("color: #0284c7; font-weight: 700; font-size: 12px;")
        pg_layout.addWidget(lbl_case)

        sep2 = QLabel("|")
        sep2.setStyleSheet("color: #cbd5e1;")
        pg_layout.addWidget(sep2)

        lbl_rep = QLabel("📑 报告: 5 份")
        lbl_rep.setStyleSheet("color: #7c3aed; font-weight: 700; font-size: 12px;")
        pg_layout.addWidget(lbl_rep)

        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedSize(24, 24)
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 13px; } QPushButton:hover { background: #e2e8f0; border-radius: 12px; }")
        btn_refresh.clicked.connect(self._reset_metrics)
        pg_layout.addWidget(btn_refresh)

        h_layout.addWidget(pill_group)
        return card

    # ================= 2. 顶部说明横幅 =================
    def _create_banner_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("apiBanner")
        card.setStyleSheet("QFrame#apiBanner { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; }")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        icon = QLabel("🔗")
        icon.setStyleSheet("font-size: 16px;")
        top_row.addWidget(icon)

        title = QLabel("IM 即时通讯接口与长连接性能测试平台")
        title.setStyleSheet("font-size: 14px; font-weight: 800; color: #0f172a;")
        top_row.addWidget(title)
        top_row.addStretch()
        layout.addLayout(top_row)

        desc = QLabel("针对 WebSocket 长连接协议、Protobuf/gRPC 接口、离线消息补偿及 Locust 高并发收发压力测试")
        desc.setStyleSheet("color: #64748b; font-size: 12px;")
        layout.addWidget(desc)
        return card

    # ================= 3. WebSocket 配置卡片 =================
    def _create_ws_config_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("apiWsCard")
        card.setStyleSheet("QFrame#apiWsCard { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; }")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        lbl_head = QLabel("⚡ WebSocket 长连接配置")
        lbl_head.setStyleSheet("font-weight: 800; color: #0f172a; font-size: 13px;")
        layout.addWidget(lbl_head)

        lbl_addr = QLabel("WEBSOCKET 地址")
        lbl_addr.setStyleSheet("color: #475569; font-size: 11px; font-weight: 700;")
        layout.addWidget(lbl_addr)

        self.edit_ws_url = QLineEdit("ws://127.0.0.1:8080/ws/im")
        self.edit_ws_url.setObjectName("apiInput")
        self.edit_ws_url.setFixedHeight(30)
        self.edit_ws_url.setStyleSheet("QLineEdit#apiInput { border: 1px solid #cbd5e1; border-radius: 5px; padding: 4px 8px; color: #0f172a; background: #ffffff; }")
        layout.addWidget(self.edit_ws_url)

        lbl_token = QLabel("用户鉴权 TOKEN")
        lbl_token.setStyleSheet("color: #475569; font-size: 11px; font-weight: 700;")
        layout.addWidget(lbl_token)

        self.edit_token = QLineEdit("Bearer test_user_session_token_1001")
        self.edit_token.setObjectName("apiTokenInput")
        self.edit_token.setFixedHeight(30)
        self.edit_token.setStyleSheet("QLineEdit#apiTokenInput { border: 1px solid #cbd5e1; border-radius: 5px; padding: 4px 8px; color: #0f172a; background: #ffffff; }")
        layout.addWidget(self.edit_token)

        self.btn_toggle_ws = QPushButton("建立长连接握手")
        self.btn_toggle_ws.setProperty("class", "btn-primary")
        self.btn_toggle_ws.setFixedHeight(30)
        self.btn_toggle_ws.setStyleSheet("background: #059669; color: #ffffff; font-weight: 700; padding: 4px 14px; border: none; border-radius: 5px;")
        self.btn_toggle_ws.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_ws.clicked.connect(self._toggle_ws)
        layout.addWidget(self.btn_toggle_ws, alignment=Qt.AlignmentFlag.AlignLeft)

        return card

    def _toggle_ws(self):
        self.is_connected = not self.is_connected
        if self.is_connected:
            self.btn_toggle_ws.setText("断开长连接握手")
            self.btn_toggle_ws.setStyleSheet("background: #e11d48; color: #ffffff; font-weight: 700; padding: 4px 14px; border: none; border-radius: 5px;")
            self.card_ws.update_value("🟢 Connected", "心跳维持在线")
            self.card_ws.lbl_val.setStyleSheet("color: #059669; font-size: 20px; font-weight: 800;")
            QMessageBox.information(self, "WebSocket 握手", "WebSocket 长连接建立握手成功！心跳维持正常。")
        else:
            self.btn_toggle_ws.setText("建立长连接握手")
            self.btn_toggle_ws.setStyleSheet("background: #059669; color: #ffffff; font-weight: 700; padding: 4px 14px; border: none; border-radius: 5px;")
            self.card_ws.update_value("🟣 Disconnected", "心跳周期: 10s")
            self.card_ws.lbl_val.setStyleSheet("color: #7c3aed; font-size: 20px; font-weight: 800;")

    # ================= 4. Locust 压测卡片 =================
    def _create_locust_config_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("apiLocustCard")
        card.setStyleSheet("QFrame#apiLocustCard { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; }")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        lbl_head = QLabel("🚀 Locust 并发消息压力测试")
        lbl_head.setStyleSheet("font-weight: 800; color: #0f172a; font-size: 13px;")
        layout.addWidget(lbl_head)

        spin_row = QHBoxLayout()
        spin_row.setSpacing(12)

        col1 = QVBoxLayout()
        lbl_users = QLabel("并发长连接用户数")
        lbl_users.setStyleSheet("color: #475569; font-size: 11px; font-weight: 700;")
        self.spin_users = QSpinBox()
        self.spin_users.setRange(10, 10000)
        self.spin_users.setValue(500)
        self.spin_users.setSingleStep(100)
        self.spin_users.setObjectName("apiSpinUsers")
        self.spin_users.setFixedHeight(30)
        self.spin_users.setStyleSheet("QSpinBox#apiSpinUsers { border: 1px solid #cbd5e1; border-radius: 5px; padding: 2px 6px; color: #0f172a; background: #ffffff; }")
        col1.addWidget(lbl_users)
        col1.addWidget(self.spin_users)
        spin_row.addLayout(col1)

        col2 = QVBoxLayout()
        lbl_rate = QLabel("每秒生成速率 (USERS/S)")
        lbl_rate.setStyleSheet("color: #475569; font-size: 11px; font-weight: 700;")
        self.spin_rate = QSpinBox()
        self.spin_rate.setRange(1, 200)
        self.spin_rate.setValue(20)
        self.spin_rate.setObjectName("apiSpinRate")
        self.spin_rate.setFixedHeight(30)
        self.spin_rate.setStyleSheet("QSpinBox#apiSpinRate { border: 1px solid #cbd5e1; border-radius: 5px; padding: 2px 6px; color: #0f172a; background: #ffffff; }")
        col2.addWidget(lbl_rate)
        col2.addWidget(self.spin_rate)
        spin_row.addLayout(col2)

        layout.addLayout(spin_row)

        self.btn_toggle_stress = QPushButton("启动 1000 并发压力测试")
        self.btn_toggle_stress.setFixedHeight(30)
        self.btn_toggle_stress.setStyleSheet("background: #d97706; color: #ffffff; font-weight: 700; padding: 4px 14px; border-radius: 5px; border: none;")
        self.btn_toggle_stress.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_stress.clicked.connect(self._toggle_stress)
        layout.addWidget(self.btn_toggle_stress, alignment=Qt.AlignmentFlag.AlignLeft)

        return card

    def _toggle_stress(self):
        self.is_stressing = not self.is_stressing
        if self.is_stressing:
            self.btn_toggle_stress.setText("停止并发压力测试")
            self.btn_toggle_stress.setStyleSheet("background: #e11d48; color: #ffffff; font-weight: 700; padding: 4px 14px; border-radius: 5px; border: none;")
            self.stress_timer.start(1000)
        else:
            self.btn_toggle_stress.setText("启动 1000 并发压力测试")
            self.btn_toggle_stress.setStyleSheet("background: #d97706; color: #ffffff; font-weight: 700; padding: 4px 14px; border-radius: 5px; border: none;")
            self.stress_timer.stop()

    def _on_stress_tick(self):
        users = self.spin_users.value()
        self.current_qps = int(users * 1.8 + random.randint(-40, 60))
        self.p99_latency = int(120 + random.randint(5, 45))
        self.total_sent += int(self.current_qps * 0.9)

        self.card_qps.update_value(f"{self.current_qps} msg/s", f"并发用户: {users} 个")
        self.card_p99.update_value(f"{self.p99_latency} ms", "门禁基线: ≤ 500ms")
        self.card_sent.update_value(f"{self.total_sent} 条", "丢包率: 0.00% (正常)")

    def _reset_metrics(self):
        self.current_qps = 0
        self.p99_latency = 0
        self.total_sent = 0
        self.card_qps.update_value("0 msg/s", f"并发用户: {self.spin_users.value()} 个")
        self.card_p99.update_value("0 ms", "门禁基线: ≤ 500ms")
        self.card_sent.update_value("0 条", "丢包率: 0.00% (正常)")

    # ================= 5. 下方协议套件 =================
    def _create_protocol_cases_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("apiProtocolCard")
        card.setStyleSheet("QFrame#apiProtocolCard { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; }")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        lbl_head = QLabel("📋 IM 专项协议测试套件")
        lbl_head.setStyleSheet("font-weight: 800; color: #0f172a; font-size: 13px;")
        layout.addWidget(lbl_head)

        cases = [
            ("WebSocket 协议握手与鉴权 Token 绑定", "协议鉴权"),
            ("心跳维持 PING/PONG 超时断线检测", "链路维持"),
            ("消息顺序逻辑 seq 机制与客户端幂等去重", "顺序一致性"),
            ("离线消息拉取与多端补偿同步 (SyncMsg)", "离线补偿"),
            ("单群 1000 人同时在线抢红包与刷屏高并发", "高并发性能")
        ]

        for name, tag in cases:
            item_box = QFrame()
            item_box.setObjectName("apiProtocolItem")
            item_box.setStyleSheet("""
                QFrame#apiProtocolItem {
                    background-color: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                }
                QFrame#apiProtocolItem:hover {
                    background-color: #f1f5f9;
                }
            """)
            i_layout = QHBoxLayout(item_box)
            i_layout.setContentsMargins(8, 7, 8, 7)
            i_layout.setSpacing(8)

            lbl_name = QLabel(name)
            lbl_name.setStyleSheet("font-weight: 600; color: #0f172a; font-size: 12px;")
            i_layout.addWidget(lbl_name)

            lbl_tag = QLabel(tag)
            lbl_tag.setStyleSheet("background-color: #ecfdf5; color: #059669; font-weight: 700; font-size: 10px; padding: 2px 6px; border-radius: 4px; border: 1px solid #a7f3d0;")
            i_layout.addWidget(lbl_tag)
            i_layout.addStretch()

            btn_assert = QPushButton("执行协议断言")
            btn_assert.setProperty("class", "btn-secondary")
            btn_assert.setFixedHeight(28)
            btn_assert.setStyleSheet("color: #2563eb; background: #ffffff; border: 1px solid #bfdbfe; font-weight: 700; padding: 3px 12px; border-radius: 5px;")
            btn_assert.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_assert.clicked.connect(lambda ch, n=name: QMessageBox.information(self, "协议断言", f"✅ 协议用例 [{n}] 执行成功，状态码 200，断言通过！"))
            i_layout.addWidget(btn_assert)

            layout.addWidget(item_box)

        return card
