from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator

class ChatLongPressLocator:
    PACKAGE_ID = CommonLocator.PACKAGE_ID
    
    # 长按菜单容器
    LONG_PRESS_MENU_CONTAINER = (AppiumBy.ID, f"{PACKAGE_ID}/gv_menu")
    
    # 菜单项文本定位
    COLLECTION = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("收藏")')
    FORWARD = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("转发")')
    MULTI_SELECT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("多选")')
    REPLY = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("回复")')
    DELETE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("删除")')
    REVOKE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("撤回")')
    COPY = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("复制")')
    ADD_EMOJI = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("添加表情")')

    # ===========================
    # 媒体类型定位（用于根据消息类型过滤气泡）
    # 注意：这些定位器基于您的 XML 结构，请根据实际情况调整
    # ===========================
    MEDIA_TYPE_MAP = {
        "text": (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description(".*text.*")'),
        "image": (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description(".*image.*")'),
        "video": (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description(".*video.*")'),
        "file": (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description(".*file.*")'),
        "card": (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description(".*card.*")'),
        "position": (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description(".*position.*")'),
    }

    # 弹窗定位器
    BTN_CONFIRM = CommonLocator.DIALOG_CONFIRM_BTN      # 确定
    BTN_CANCEL = CommonLocator.DIALOG_CANCEL_BTN        # 取消

    @staticmethod
    def get_menu_item_by_name(name: str):
        """动态生成菜单项定位器"""
        return (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{name}")')
