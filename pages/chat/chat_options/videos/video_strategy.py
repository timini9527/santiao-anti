from dataclasses import dataclass
from typing import List

@dataclass
class VideoSelectMode:
    mode: int
    desc: str

@dataclass
class VideoSendOption:
    use_preview: bool
    use_original: bool
    desc: str

@dataclass
class BatchVideoScenario:
    count: int
    desc: str

# 1. 单选模式
VIDEO_SELECT_MODES = [
    VideoSelectMode(0, "选择后取消(点两次)"),
    VideoSelectMode(1, "相册第一条视频"),
    VideoSelectMode(2, "随机选择视频"),
    VideoSelectMode(3, "滑到底部后的最后一条视频"),
    VideoSelectMode(4, "第9张(不够则下滑寻找，仍不足则选最后一张)")
]

# 2. 发送选项 (大部分 IM 视频原图涉及转码，这里保留接口供校验)
VIDEO_SEND_OPTIONS = [
    VideoSendOption(False, False, "直接发送"),
    VideoSendOption(True, False, "预览后发送"),
    VideoSendOption(False, True, "开启高清/原图发送")
]

# 3. 批量场景
BATCH_VIDEO_SCENARIOS = [
    BatchVideoScenario(3, "批量选 3 条视频发送"),
    BatchVideoScenario(9, "上限测试：批量选 9 条视频")
]
