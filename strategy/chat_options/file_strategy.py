from dataclasses import dataclass


@dataclass
class FileCategoryScenario:
    """
    文件分类测试场景：定义分类入口、底层文件类型及优先探测目录
    """
    sub_menu_item: str      # UI 界面分类名称（如 '图片'、'视频'、'音频'、'文档'）
    file_type: str          # 内部业务类型映射（如 'image'、'video'、'audio'、'document'）
    dir_name: str           # 优先探测的目录/相册名称（如 'santiaoTalk'、'Music'、'File'）
    desc: str               # 用于 Allure 报告和 pytest ids 显示

    def __str__(self):
        return self.desc


# ==================== 文件分类场景实例 ====================
CATEGORY_IMAGE    = FileCategoryScenario(sub_menu_item="图片", file_type="image",    dir_name="santiaoTalk", desc="图片分类")
CATEGORY_VIDEO    = FileCategoryScenario(sub_menu_item="视频", file_type="video",    dir_name="santiaoTalk", desc="视频分类")
CATEGORY_AUDIO    = FileCategoryScenario(sub_menu_item="音频", file_type="audio",    dir_name="Music",       desc="音频分类")
CATEGORY_DOCUMENT = FileCategoryScenario(sub_menu_item="文档", file_type="document", dir_name="File",        desc="文档分类")

FILE_CATEGORIES = [CATEGORY_IMAGE, CATEGORY_VIDEO, CATEGORY_AUDIO, CATEGORY_DOCUMENT]


@dataclass
class FileSelectMode:
    """
    文件选择模式策略：决定在文件列表中的选取模式及索引
    """
    mode: str               # 选中模式 ('first', 'last', 'index', 'absolute_last')
    target_index: int       # 模式关联的目标索引（mode='index' 时有效，默认 0）
    desc: str               # 用于 Allure 报告和 pytest ids 显示

    def __str__(self):
        return self.desc


# ==================== 文件选取模式实例 ====================
SELECT_FIRST_FILE         = FileSelectMode(mode="first",         target_index=0, desc="首个文件")
SELECT_LAST_FILE          = FileSelectMode(mode="last",          target_index=0, desc="列表末尾文件")
SELECT_SECOND_FILE        = FileSelectMode(mode="index",         target_index=1, desc="第2个文件(索引1)")
SELECT_ABSOLUTE_LAST_FILE = FileSelectMode(mode="absolute_last", target_index=0, desc="刷底最后一个文件")

FILE_SELECT_MODES = [SELECT_FIRST_FILE, SELECT_LAST_FILE, SELECT_SECOND_FILE, SELECT_ABSOLUTE_LAST_FILE]


@dataclass
class ExactFileScenario:
    """
    固定文件名搜索测试场景：用于精准搜索和强一致性断言
    """
    exact_file_name: str    # 完整固定文件名（包含后缀）
    desc: str               # 用于 Allure 报告和 pytest ids 显示

    def __str__(self):
        return self.desc


# ==================== 固定文件名场景实例 ====================
EXACT_IMAGE = ExactFileScenario(exact_file_name="测试-图片.jpg",        desc="固定图片文件")
EXACT_VIDEO = ExactFileScenario(exact_file_name="测试-视频.mp4",        desc="固定视频文件")
EXACT_DOC   = ExactFileScenario(exact_file_name="测试-文档-12345.pdf",  desc="固定PDF文档")
EXACT_AUDIO = ExactFileScenario(exact_file_name="测试-音乐.ogg",        desc="固定音频文件")

EXACT_FILE_SCENARIOS = [EXACT_IMAGE, EXACT_VIDEO, EXACT_DOC, EXACT_AUDIO]
