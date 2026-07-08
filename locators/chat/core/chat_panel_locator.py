from appium.webdriver.common.appiumby import AppiumBy
from locators.system.common.common_locator import CommonLocator

class ChatPanelLocator(CommonLocator):
    """聊天页面“+”号扩展面板的元素定位器"""
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 扩展面板主容器
    INPUT_MORE_PAGER = (AppiumBy.ID, f'{PACKAGE_ID}/input_more_pager')

    # 扩展面板主容器 - 功能
    LL_INPUT_MORE = (AppiumBy.ID, f'{PACKAGE_ID}/llInputMore')

    # 面板按钮项根容器 ID
    MORE_ACTION_ROOT_ID = f'{PACKAGE_ID}/more_action_root'
    MORE_ACTION_ROOT = (AppiumBy.ID, MORE_ACTION_ROOT_ID)

    # 面板按钮项文本 ID
    MORE_ACTION_TEXT_ID = f'{PACKAGE_ID}/more_action_text'
    MORE_ACTION_TEXT = (AppiumBy.ID, MORE_ACTION_TEXT_ID)

    # 常用功能项的静态 XPath 定位
    BTN_FILE = (AppiumBy.XPATH, f'//*[@resource-id="{MORE_ACTION_ROOT_ID}" and .//*[@resource-id="{MORE_ACTION_TEXT_ID}" and @text="文件"]]')
    BTN_VOTE = (AppiumBy.XPATH, f'//*[@resource-id="{MORE_ACTION_ROOT_ID}" and .//*[@resource-id="{MORE_ACTION_TEXT_ID}" and @text="投票"]]')
    BTN_SOLITAIRE = (AppiumBy.XPATH, f'//*[@resource-id="{MORE_ACTION_ROOT_ID}" and .//*[@resource-id="{MORE_ACTION_TEXT_ID}" and @text="接龙"]]')
    BTN_COLLECTION = (AppiumBy.XPATH, f'//*[@resource-id="{MORE_ACTION_ROOT_ID}" and .//*[@resource-id="{MORE_ACTION_TEXT_ID}" and @text="收藏"]]')
    BTN_CARD = (AppiumBy.XPATH, f'//*[@resource-id="{MORE_ACTION_ROOT_ID}" and .//*[@resource-id="{MORE_ACTION_TEXT_ID}" and @text="名片"]]')
    BTN_LOCATION = (AppiumBy.XPATH, f'//*[@resource-id="{MORE_ACTION_ROOT_ID}" and .//*[@resource-id="{MORE_ACTION_TEXT_ID}" and @text="位置"]]')
    BTN_VIDEO_CALL = (AppiumBy.XPATH, f'//*[@resource-id="{MORE_ACTION_ROOT_ID}" and .//*[@resource-id="{MORE_ACTION_TEXT_ID}" and @text="通话"]]')
    BTN_ALBUM = (AppiumBy.XPATH, f'//*[@resource-id="{MORE_ACTION_ROOT_ID}" and .//*[@resource-id="{MORE_ACTION_TEXT_ID}" and @text="图片"]]')
    BTN_CAMERA = (AppiumBy.XPATH, f'//*[@resource-id="{MORE_ACTION_ROOT_ID}" and .//*[@resource-id="{MORE_ACTION_TEXT_ID}" and @text="拍摄"]]')

    @classmethod
    def get_panel_item_by_text(cls, text: str) -> tuple:
        """根据动态文本获取对应的面板按钮项"""
        return (AppiumBy.XPATH, f'//*[@resource-id="{cls.MORE_ACTION_ROOT_ID}" and .//*[@resource-id="{cls.MORE_ACTION_TEXT_ID}" and @text="{text}"]]')
