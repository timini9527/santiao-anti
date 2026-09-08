from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


class GroupDetailLocator(CommonLocator):
    """群资料页面定位器 (严格基于真实 Android XML 节点树)"""

    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # =========================================================================
    # 1. 顶部导航栏
    # =========================================================================
    IV_BACK = CommonLocator.TOP_IV_BACK_BTN                                     # 返回按钮
    TV_TITLE = CommonLocator.TOP_TV_TITLE                                       # 页面标题 ("群资料")

    # =========================================================================
    # 2. 页面内容区域 (ScrollView)
    # =========================================================================
    CONTENT_SCROLL = (AppiumBy.ID, f"{PACKAGE_ID}/content_scroll")              # 内容滚动容器
    GROUP_NAME = (AppiumBy.ID, f"{PACKAGE_ID}/group_name")                      # 群名称 (如 "测试群aaaaa")

    # 群 ID 区域
    GROUP_ID_ROW = (AppiumBy.ID, f"{PACKAGE_ID}/group_id_row")                  # 群 ID 容器行
    GROUP_ID_TEXT = (AppiumBy.ID, f"{PACKAGE_ID}/group_id_text")                # 群 ID 文本 (如 "群ID:284631016")
    GROUP_ID_COPY = (AppiumBy.ID, f"{PACKAGE_ID}/group_id_copy")                # 复制群 ID 图标

    # 群标签区域 (ViewGroup)
    GROUP_TAGS = (AppiumBy.ID, f"{PACKAGE_ID}/group_tags")                      # 群标签容器
    GROUP_TAG_ITEMS = (AppiumBy.XPATH, f'//*[@resource-id="{PACKAGE_ID}/group_tags"]//android.widget.TextView') # 标签集合

    # =========================================================================
    # 3. 底部主操作按钮
    # =========================================================================
    GROUP_ADD = (AppiumBy.ID, f"{PACKAGE_ID}/group_add")                        # 底部大按钮 ("发送消息" / "加入群聊")

    # 兼容性别名
    GROUP_ID = GROUP_ID_TEXT
    IV_COPY_ID = GROUP_ID_COPY
    BTN_ACTION = GROUP_ADD
