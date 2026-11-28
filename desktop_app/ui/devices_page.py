# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 (原生桌面端) - 设备矩阵页面
=======================================================
1:1 像素级复刻图 4 (DevicesPlatform.vue)：
1. 顶部 Header：设备矩阵 控制台 + 多设备拓扑与 Appium 服务实时监控 + 右侧药丸 Badges
2. 说明横幅卡片：移动端自动化设备矩阵与环境中心
3. Appium 服务拓扑行：:4723 (主叫发送端) 与 :4724 (被叫接收端) 状态监控卡片 (支持真实拉起与连通性测量)
4. 在线测试设备池 (7 台)：多卡片 Grid 布局，支持真实 USB 真机与模拟器卡片展示、重新扫描与详细规格查看
"""
import os
import sys
import time
import shutil
import socket
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_CURRENT_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

try:
    from ..core.device_manager import DeviceManager
    from ..core.path_resolver import SmartPathResolver
    from ..core.report_scanner import get_reports_count
except (ImportError, ValueError):
    from desktop_app.core.device_manager import DeviceManager
    from desktop_app.core.path_resolver import SmartPathResolver
    from desktop_app.core.report_scanner import get_reports_count


def _get_lan_ip() -> str:
    """获取本机真实有效局域网 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "172.18.0.1"


class DeviceCard(QFrame):
    """目标布局中的紧凑设备卡片 (支持点击查看详情与一键复制 UDID)"""

    def __init__(self, dev_type: str, udid: str, driver: str = "Android (UIAutomator2)", port: str = "http://127.0.0.1:4724", res: str = "1080x2400", parent=None):
        super().__init__(parent)
        self.dev_type = dev_type
        self.udid = udid
        self.driver = driver
        self.port = port
        self.res = res

        self.setObjectName("deviceCard")
        self.setStyleSheet("""
            QFrame#deviceCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            QFrame#deviceCard:hover {
                border-color: #93c5fd;
                background-color: #f8fafc;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(9)

        # 顶部：手机图标 + 设备类型 + 就绪按钮
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        icon_box = QFrame()
        icon_box.setFixedSize(32, 32)
        icon_box.setObjectName("deviceIconBox")
        icon_box.setStyleSheet("QFrame#deviceIconBox { background-color: #eff6ff; border: none; border-radius: 7px; }")
        ib_layout = QVBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        lbl_icon = QLabel("📱")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setStyleSheet("font-size: 16px;")
        ib_layout.addWidget(lbl_icon)
        top_row.addWidget(icon_box)

        name_box = QVBoxLayout()
        name_box.setSpacing(1)
        lbl_name = QLabel(f"({dev_type})")
        lbl_name.setStyleSheet("font-weight: 700; color: #0f172a; font-size: 12px; background: transparent; border: none;")
        lbl_udid = QLabel(f"UDID: {udid}")
        lbl_udid.setStyleSheet("color: #64748b; font-size: 10px; font-family: monospace; background: transparent; border: none;")
        name_box.addWidget(lbl_name)
        name_box.addWidget(lbl_udid)
        top_row.addLayout(name_box)

        top_row.addStretch()

        btn_ready = QPushButton("就绪")
        btn_ready.setToolTip(f"点击查看设备【{udid}】详细规格与复制识别码")
        btn_ready.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ready.setStyleSheet("""
            QPushButton {
                background-color: #ecfdf5;
                color: #059669;
                border: 1px solid #a7f3d0;
                border-radius: 4px;
                padding: 2px 8px;
                font-weight: 700;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #d1fae5;
                border-color: #6ee7b7;
            }
        """)
        btn_ready.clicked.connect(self._show_device_info)
        top_row.addWidget(btn_ready)

        layout.addLayout(top_row)
        layout.addSpacing(2)

        # 规格列表
        specs = [
            ("驱动系统:", driver),
            ("绑定端口:", port),
            ("分辨率:", res)
        ]
        for k, v in specs:
            s_row = QHBoxLayout()
            s_row.setSpacing(4)
            lbl_k = QLabel(k)
            lbl_k.setStyleSheet("color: #64748b; font-size: 10px; background: transparent; border: none;")
            lbl_v = QLabel(v)
            lbl_v.setStyleSheet("color: #0f172a; font-size: 10px; font-weight: 600; font-family: monospace; background: transparent; border: none;")
            s_row.addWidget(lbl_k)
            s_row.addStretch()
            s_row.addWidget(lbl_v)
            layout.addLayout(s_row)

    def _show_device_info(self, *args):
        """展示设备详细信息弹窗并自动复制 UDID"""
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.udid)
        QMessageBox.information(
            self,
            "设备连接详情",
            f"📱 设备类型: {self.dev_type}\n"
            f"🆔 设备识别码 (UDID): {self.udid}\n"
            f"🔧 底层驱动系统: {self.driver}\n"
            f"🌐 映射服务端口: {self.port}\n"
            f"🖥️ 物理屏幕分辨率: {self.res}\n"
            f"🟢 运行状态: 就绪可用 (Ready)\n\n"
            f"✅ 设备识别码已自动复制到剪贴板！"
        )


class DevicesPage(QWidget):
    """设备矩阵与环境中心工作台 (图 4 像素级复刻)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lan_ip = _get_lan_ip()
        self.appium_status_labels: Dict[int, QLabel] = {}
        self.init_ui()
        # 懒加载策略：推迟至首屏呈现后异步非阻塞探测设备池，绝不阻塞应用启动首屏
        QTimer.singleShot(400, lambda: self.refresh_devices(show_toast=False))
        # 延时自动异步检测一次两个 Appium 端口的真实连通状态
        QTimer.singleShot(650, self._detect_all_appium_status)

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 8, 10, 10)
        root_layout.setSpacing(10)

        # 1. 顶部 Header
        top_header = self._create_top_header()
        root_layout.addWidget(top_header)

        # 2. 滚动内容区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 2.1 顶部说明横幅卡片
        banner = self._create_banner_card()
        layout.addWidget(banner)

        # 2.2 Appium 服务状态两列横排卡片
        appium_row = QHBoxLayout()
        appium_row.setSpacing(14)

        self.card_appium1 = self._create_appium_card(4723, "主叫发送端 (Device 1)")
        self.card_appium2 = self._create_appium_card(4724, "被叫接收端 (Device 2)")

        appium_row.addWidget(self.card_appium1, stretch=5)
        appium_row.addWidget(self.card_appium2, stretch=5)
        layout.addLayout(appium_row)

        # 2.3 设备池卡片 (包含刷新扫描 USB 设备按钮与 7 台设备网格)
        devices_pool_card = self._create_devices_pool_card()
        layout.addWidget(devices_pool_card)

        scroll.setWidget(content)
        root_layout.addWidget(scroll, stretch=1)

    # ================= 1. 顶部 Header =================
    def _create_top_header(self) -> QWidget:
        card = QFrame()
        card.setObjectName("devicesTopHeader")
        card.setStyleSheet("QFrame#devicesTopHeader { background-color: #ffffff; border-bottom: 1px solid #e2e8f0; }")
        h_layout = QHBoxLayout(card)
        h_layout.setContentsMargins(2, 2, 2, 6)
        h_layout.setSpacing(12)

        icon_box = QFrame()
        icon_box.setFixedSize(36, 36)
        icon_box.setStyleSheet("background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px;")
        ib_layout = QVBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        lbl_icon = QLabel("⚙️")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setStyleSheet("font-size: 18px;")
        ib_layout.addWidget(lbl_icon)
        h_layout.addWidget(icon_box)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        lbl_main = QLabel("设备矩阵 控制台")
        lbl_main.setStyleSheet("font-size: 15px; font-weight: 800; color: #0f172a;")
        lbl_sub = QLabel("多设备拓扑与 Appium 服务实时监控")
        lbl_sub.setStyleSheet("font-size: 11px; color: #64748b;")
        title_box.addWidget(lbl_main)
        title_box.addWidget(lbl_sub)
        h_layout.addLayout(title_box)

        h_layout.addStretch()

        pill_group = QFrame()
        pill_group.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 20px; padding: 2px 6px;")
        pg_layout = QHBoxLayout(pill_group)
        pg_layout.setContentsMargins(6, 2, 6, 2)
        pg_layout.setSpacing(10)

        self.lbl_dev = QLabel("🟢 设备: 1 台在线")
        self.lbl_dev.setStyleSheet("color: #059669; font-weight: 700; font-size: 12px;")
        pg_layout.addWidget(self.lbl_dev)

        sep1 = QLabel("|")
        sep1.setStyleSheet("color: #cbd5e1;")
        pg_layout.addWidget(sep1)

        lbl_case = QLabel("✏️ 用例: 1383 条")
        lbl_case.setStyleSheet("color: #0284c7; font-weight: 700; font-size: 12px;")
        pg_layout.addWidget(lbl_case)

        sep2 = QLabel("|")
        sep2.setStyleSheet("color: #cbd5e1;")
        pg_layout.addWidget(sep2)

        self.lbl_report_pill = QLabel(f"📑 报告: {get_reports_count()} 份")
        self.lbl_report_pill.setStyleSheet("color: #7c3aed; font-weight: 700; font-size: 12px;")
        pg_layout.addWidget(self.lbl_report_pill)

        btn_refresh = QPushButton("🔄")
        btn_refresh.setToolTip("重新检测设备与服务连通性")
        btn_refresh.setFixedSize(24, 24)
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 13px; } QPushButton:hover { background: #e2e8f0; border-radius: 12px; }")
        btn_refresh.clicked.connect(lambda checked=False: self.refresh_devices(show_toast=True))
        pg_layout.addWidget(btn_refresh)

        h_layout.addWidget(pill_group)
        return card

    # ================= 2. 顶部说明横幅 =================
    def _create_banner_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("devicesBanner")
        card.setStyleSheet("QFrame#devicesBanner { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; }")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(7)

        top_row = QHBoxLayout()
        icon = QLabel("⚙️")
        icon.setStyleSheet("font-size: 16px; color: #7c3aed;")
        top_row.addWidget(icon)

        title = QLabel("移动端自动化设备矩阵与环境中心")
        title.setStyleSheet("font-size: 14px; font-weight: 800; color: #0f172a;")
        top_row.addWidget(title)
        top_row.addStretch()
        layout.addLayout(top_row)

        desc = QLabel("集中管理 Android / iOS / 鸿蒙物理设备池，监控 Appium 服务拓扑，提供双机联调映射与自适应能力")
        desc.setStyleSheet("color: #64748b; font-size: 12px;")
        layout.addWidget(desc)
        return card

    # ================= 3. Appium 服务拓扑卡片 =================
    def _create_appium_card(self, port: int, role: str) -> QWidget:
        card = QFrame()
        card.setObjectName(f"appiumCard{port}")
        card.setStyleSheet(f"QFrame#appiumCard{port} {{ background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; }}")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 13, 18, 13)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        lbl_title = QLabel(f"Appium Server :{port}")
        lbl_title.setStyleSheet("font-weight: 800; color: #0f172a; font-size: 13px;")
        top_row.addWidget(lbl_title)
        top_row.addStretch()

        lbl_active = QLabel("检测中...")
        lbl_active.setStyleSheet("background-color: #f1f5f9; color: #64748b; border: 1px solid #cbd5e1; border-radius: 4px; padding: 2px 6px; font-weight: 700; font-size: 10px;")
        self.appium_status_labels[port] = lbl_active
        top_row.addWidget(lbl_active)
        layout.addLayout(top_row)

        lbl_role = QLabel(role)
        lbl_role.setStyleSheet("color: #2563eb; font-size: 11px; font-weight: 600;")
        layout.addWidget(lbl_role)

        lbl_listen = QLabel(f"在线监听: {self.lan_ip}:{port}")
        lbl_listen.setStyleSheet("color: #60a5fa; font-size: 11px; font-family: monospace;")
        layout.addWidget(lbl_listen)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_start = QPushButton("一键拉起服务")
        btn_start.setToolTip(f"启动端口 {port} 对应的 Appium 服务")
        btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_start.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-size: 11px;
                font-weight: 700;
                padding: 5px 14px;
                border: 1px solid #1d4ed8;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)
        btn_start.clicked.connect(lambda checked=False, p=port: self._on_start_appium(p))
        btn_row.addWidget(btn_start)

        btn_detect = QPushButton("探测连通性")
        btn_detect.setToolTip(f"探测端口 {port} 实际网络延迟与连通状态")
        btn_detect.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_detect.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #334155;
                font-size: 11px;
                font-weight: 600;
                padding: 4px 14px;
                border: 1px solid #cbd5e1;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f8fafc;
                border-color: #94a3b8;
                color: #0f172a;
            }
            QPushButton:pressed {
                background-color: #f1f5f9;
            }
        """)
        btn_detect.clicked.connect(lambda checked=False, p=port: self._on_detect_appium(p))
        btn_row.addWidget(btn_detect)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        return card

    # ================= 4. Appium 实际控制与探测逻辑 =================
    def _check_appium_alive(self, port: int) -> tuple[bool, float]:
        """真实测试端口连通性并计算往返延时 (ms)"""
        t0 = time.perf_counter()
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.8):
                latency = (time.perf_counter() - t0) * 1000
                return True, max(latency, 1.0)
        except Exception:
            return False, 0.0

    def _update_appium_card_status(self, port: int, is_alive: bool):
        lbl = self.appium_status_labels.get(port)
        if not lbl:
            return
        if is_alive:
            lbl.setText("运行中 (Active)")
            lbl.setStyleSheet("background-color: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; border-radius: 4px; padding: 2px 6px; font-weight: 700; font-size: 10px;")
        else:
            lbl.setText("未启动 (Inactive)")
            lbl.setStyleSheet("background-color: #f1f5f9; color: #64748b; border: 1px solid #cbd5e1; border-radius: 4px; padding: 2px 6px; font-weight: 700; font-size: 10px;")

    def _detect_all_appium_status(self):
        """批量静默刷新所有 Appium 卡片状态"""
        for port in [4723, 4724]:
            alive, _ = self._check_appium_alive(port)
            self._update_appium_card_status(port, alive)

    def _on_start_appium(self, port: int):
        """一键拉起 Appium 服务"""
        alive, _ = self._check_appium_alive(port)
        if alive:
            QMessageBox.information(
                self, "Appium 服务",
                f"Appium Server (端口 {port}) 当前已处于活跃运行状态！\n无需重复拉起服务。"
            )
            self._update_appium_card_status(port, True)
            return

        # 动态定位 start_appium_batch.bat 批处理文件
        project_root = Path(SmartPathResolver.get_project_root())
        candidates = [
            Path(sys.executable).parent / "start_appium_batch.bat",
            project_root / "start_appium_batch.bat",
            Path.cwd() / "start_appium_batch.bat"
        ]
        bat_file: Optional[Path] = None
        for c in candidates:
            if c.is_file():
                bat_file = c
                break

        try:
            if bat_file and sys.platform == "win32":
                os.startfile(str(bat_file))
                msg = f"▶ 已在独立控制台窗口拉起 Appium 批量服务脚本: {bat_file.name}\n(包含端口 {port})"
            elif sys.platform == "win32":
                subprocess.Popen(["appium", "server", "-p", str(port)], shell=True)
                msg = f"▶ 已向系统发起拉起 Appium Server (端口 {port}) 的指令！"
            else:
                appium_bin = shutil.which("appium") or "appium"
                subprocess.Popen(
                    [appium_bin, "server", "-p", str(port)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                msg = f"▶ 已向系统发起拉起 Appium Server (端口 {port}) 的指令！"

            QMessageBox.information(
                self, "服务拉起成功",
                f"{msg}\n\n系统将在 2 秒后自动重新探测连通性状态。"
            )
            # 延时 2 秒重新检测该端口并刷新界面
            QTimer.singleShot(2000, lambda: self._on_detect_appium(port, silent=True))
        except Exception as e:
            QMessageBox.critical(self, "启动失败", f"启动 Appium 服务出现异常:\n{e}")

    def _on_detect_appium(self, port: int, silent: bool = False):
        """探测指定端口连通性"""
        alive, latency = self._check_appium_alive(port)
        self._update_appium_card_status(port, alive)

        if silent:
            return

        if alive:
            QMessageBox.information(
                self, "探测连通性成功",
                f"✅ Appium Server (端口 {port}) 连通正常！\n\n"
                f"• 监听端口: {port}\n"
                f"• 局域网接入点: {self.lan_ip}:{port}\n"
                f"• 本地通信回路: http://127.0.0.1:{port}\n"
                f"• 往返响应延时: {latency:.1f} ms\n"
                f"• 服务运行状态: 活跃就绪 (Active)"
            )
        else:
            QMessageBox.warning(
                self, "探测连通性失败",
                f"❌ Appium Server (端口 {port}) 未检测到服务响应！\n\n"
                f"当前端口未检测到正在监听的服务进程。\n"
                f"请点击【一键拉起服务】启动该服务，或检查 4723/4724 端口配置。"
            )

    # ================= 5. 在线测试设备池 =================
    def _create_devices_pool_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("devicesPoolCard")
        card.setStyleSheet("QFrame#devicesPoolCard { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; }")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        self.lbl_pool_title = QLabel("📱 在线测试设备池")
        self.lbl_pool_title.setStyleSheet("font-weight: 800; color: #0f172a; font-size: 13px;")
        header_row.addWidget(self.lbl_pool_title)
        header_row.addStretch()

        btn_scan = QPushButton("重新扫描 USB 设备")
        btn_scan.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_scan.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-size: 12px;
                font-weight: 700;
                padding: 6px 16px;
                border: 1px solid #1d4ed8;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
                border-color: #1e40af;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)
        btn_scan.clicked.connect(lambda checked=False: self.refresh_devices(show_toast=True))
        header_row.addWidget(btn_scan)
        layout.addLayout(header_row)

        # 设备网格 (Grid 排布，1:1 复刻图 4 中的真机和模拟器卡片)
        self.grid_layout = QGridLayout()
        self.grid_layout.setHorizontalSpacing(12)
        self.grid_layout.setVerticalSpacing(12)

        # 初始先进入纯动态设备网格布局
        self._render_device_grid([])
        layout.addLayout(self.grid_layout)

        return card

    @staticmethod
    def _fetch_device_resolution(adb_bin: str, udid: str, platform: str) -> str:
        """动态向 ADB 发送指令获取真实设备物理屏幕分辨率"""
        if platform != "Android":
            return "自适应"
        try:
            no_window = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            out = subprocess.check_output(
                [adb_bin, "-s", udid, "shell", "wm", "size"],
                timeout=1.5,
                creationflags=no_window
            ).decode("utf-8", errors="ignore")
            for line in out.splitlines():
                if "size:" in line:
                    return line.split("size:")[-1].strip()
        except Exception:
            pass
        return "自适应"

    def _render_device_grid(self, devices: List[Dict[str, str]]):
        """动态渲染真实在线设备池卡片网格 (无任何写死假数据)"""
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not devices:
            empty_box = QFrame()
            empty_box.setObjectName("emptyDeviceBox")
            empty_box.setStyleSheet("""
                QFrame#emptyDeviceBox {
                    background-color: #f8fafc;
                    border: 1px dashed #cbd5e1;
                    border-radius: 8px;
                    padding: 36px 20px;
                }
            """)
            e_layout = QVBoxLayout(empty_box)
            e_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            e_layout.setSpacing(8)

            lbl_empty_icon = QLabel("🔌")
            lbl_empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_empty_icon.setStyleSheet("font-size: 32px;")
            e_layout.addWidget(lbl_empty_icon)

            lbl_empty_title = QLabel("当前未检测到已连接的移动设备")
            lbl_empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_empty_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #475569;")
            e_layout.addWidget(lbl_empty_title)

            lbl_empty_desc = QLabel("请使用 USB 数据线连接手机并开启【USB 调试】，或启动 Android 模拟器，然后点击右上角【重新扫描 USB 设备】")
            lbl_empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_empty_desc.setStyleSheet("font-size: 11px; color: #94a3b8;")
            e_layout.addWidget(lbl_empty_desc)

            self.grid_layout.addWidget(empty_box, 0, 0, 1, 5)
            self.lbl_pool_title.setText("📱 在线测试设备池 (0 台在线)")
            return

        cols = 5  # 宽屏每行 5 张卡片
        for idx, dev in enumerate(devices):
            card = DeviceCard(
                dev_type=dev["type"],
                udid=dev["udid"],
                driver=dev.get("driver", "Android (UIAutomator2)"),
                port=dev.get("port", "http://127.0.0.1:4724"),
                res=dev.get("res", "自适应")
            )
            r = idx // cols
            c = idx % cols
            self.grid_layout.addWidget(card, r, c)

        self.lbl_pool_title.setText(f"📱 在线测试设备池 ({len(devices)} 台在线)")

    def refresh_devices(self, show_toast: bool = False, *args):
        """动态探测真实在线移动设备 (USB真机与模拟器)，杜绝写死假数据"""
        details = DeviceManager.scan_connected_devices()
        device_items = details.get("device_items", [])

        # 获取 ADB 工具以动态读取真实屏幕分辨率
        tools = SmartPathResolver.discover_mobile_toolchain()
        adb_bin = tools.get("adb") or "adb"

        online_devices = []
        for idx, item in enumerate(device_items):
            udid = item["udid"]
            is_real = item.get("is_real", True)
            platform = item.get("platform", "Android")
            dev_type = "USB真机" if is_real else "模拟器"
            if platform == "HarmonyOS":
                driver = "HarmonyOS (ArkTS)"
            elif platform == "iOS":
                driver = "iOS (XCUITest)"
            else:
                driver = "Android (UIAutomator2)"
            port_num = 4723 if idx == 0 else (4724 + (idx - 1))

            res = self._fetch_device_resolution(adb_bin, udid, platform)
            online_devices.append({
                "type": dev_type,
                "udid": udid,
                "driver": driver,
                "port": f"http://127.0.0.1:{port_num}",
                "res": res
            })

        # 动态渲染设备池网格
        self._render_device_grid(online_devices)

        # 动态同步更新顶部 Header 药丸
        total_online = len(online_devices)
        if total_online > 0:
            real_count = sum(1 for d in online_devices if d["type"] == "USB真机")
            self.lbl_dev.setText(f"🟢 设备: {total_online} 台在线 ({real_count} 真机)")
            self.lbl_dev.setStyleSheet("color: #059669; font-weight: 700; font-size: 12px;")
        else:
            self.lbl_dev.setText("⚪ 设备: 0 台在线")
            self.lbl_dev.setStyleSheet("color: #64748b; font-weight: 700; font-size: 12px;")

        if hasattr(self, "lbl_report_pill"):
            self.lbl_report_pill.setText(f"📑 报告: {get_reports_count()} 份")

        # 联动刷新一次 Appium 状态
        self._detect_all_appium_status()

        if show_toast:
            if total_online > 0:
                dev_lines = "\n".join(f"  • [{d['type']}] {d['udid']} ({d['res']})" for d in online_devices)
                QMessageBox.information(
                    self, "设备扫描完成",
                    f"🔍 在线设备矩阵扫描完成！\n\n"
                    f"当前检测到 {total_online} 台物理在线设备：\n{dev_lines}\n\n"
                    f"• Appium 拓扑与映射端口已同步就绪。"
                )
            else:
                QMessageBox.warning(
                    self, "未检测到在线设备",
                    "⚠ 当前未检测到任何已连接的物理真机或模拟器！\n\n"
                    "请检查：\n"
                    "1. USB 数据线是否稳定连接电脑；\n"
                    "2. 手机是否已开启【开发者选项】与【USB 调试】并完成授权；\n"
                    "3. 若使用模拟器，请确认模拟器已启动并处于运行状态。"
                )
