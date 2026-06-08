from dataclasses import dataclass


@dataclass
class ImageSelectMode:
    """
    图片选择模式策略：决定如何在相册网格中选取图片
    """
    mode: int       # 对应 ChatImagePage.select_single_image(mode=?) 的参数
    desc: str       # 用于 Allure 报告和 pytest ids 显示

    def __str__(self):
        return self.desc


# ==================== 选图模式实例 ====================
SELECT_FIRST  = ImageSelectMode(mode=1, desc="选择第一张")
SELECT_RANDOM = ImageSelectMode(mode=2, desc="随机选择")
SELECT_LAST   = ImageSelectMode(mode=3, desc="滑到底部最后一张")
SELECT_NINTH  = ImageSelectMode(mode=4, desc="选择第9张(不足则下滑查找)")

SELECT_MODES = [SELECT_FIRST, SELECT_RANDOM, SELECT_LAST, SELECT_NINTH]


@dataclass
class ImageSendOption:
    """
    图片发送选项策略：控制发送前的附加操作组合（预览/原图）
    所有行为由布尔字段驱动，测试方法体内零 if-elif 分支
    """
    name: str           # 策略唯一标识
    desc: str           # 用于 Allure 报告显示
    use_preview: bool   # 是否需要先点击预览按钮
    use_original: bool  # 是否需要勾选原图复选框

    def __str__(self):
        return self.desc

# ==================== 发送选项实例 ====================
SEND_DIRECT           = ImageSendOption(name="direct",           desc="直接发送",       use_preview=False, use_original=False)
SEND_PREVIEW          = ImageSendOption(name="preview",          desc="预览后发送",     use_preview=True,  use_original=False)
SEND_ORIGINAL         = ImageSendOption(name="original",         desc="原图发送",       use_preview=False, use_original=True)
SEND_PREVIEW_ORIGINAL = ImageSendOption(name="preview_original", desc="预览+原图发送",  use_preview=True,  use_original=True)

SEND_OPTIONS = [SEND_DIRECT, SEND_PREVIEW, SEND_ORIGINAL, SEND_PREVIEW_ORIGINAL]


@dataclass
class BatchImageScenario:
    desc: str
    count: int
    use_preview: bool
    use_original: bool
    verify_preview_swipe: bool = False

    def __str__(self):
        return self.desc

BATCH_IMAGE_SCENARIOS = [
    BatchImageScenario("批量3张-直接发送", 3, False, False),
    BatchImageScenario("批量3张-原图发送", 3, False, True),
    BatchImageScenario("批量3张-预览后发送", 3, True, False, True),
    BatchImageScenario("批量3张-预览+原图发送", 3, True, True, True),
    BatchImageScenario("批量9张-直接发送", 9, False, False),
    BatchImageScenario("批量9张-预览+原图发送", 9, True, True, True),
]





