from appium.webdriver.common.appiumby import AppiumBy
from locators.system.common.common_locator import CommonLocator

class ChatContactCardLocator(CommonLocator):
    """名片模块特有定位器 (仅保留名片入口及消息气泡相关)"""
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # ==================== 名片入口（加号面板内）====================
    CONTACT_CARD_BTN_ID = f'{PACKAGE_ID}/imCardIcon'
    CONTACT_CARD_BTN = (AppiumBy.ID, CONTACT_CARD_BTN_ID)

    
    CONTACT_CARD_ROOT_ID = f'{PACKAGE_ID}/more_action_root'
    CONTACT_CARD_CONTENT_ID = f'{PACKAGE_ID}/more_action_content'
    CONTACT_CARD_ROOT = (AppiumBy.XPATH, f'//*[@resource-id="{CONTACT_CARD_ROOT_ID}" and .//*[@text="名片"]]')

    # ==================== 群聊名片详情 ====================
    
    # 群头像
    GROUP_CARD_AVATAR = (AppiumBy.ID, f'{PACKAGE_ID}/group_avatar')
    # 群名称
    GROUP_CARD_NAME = (AppiumBy.ID, f'{PACKAGE_ID}/group_name')
    # 群成员数量
    GROUP_CARD_MEMBER_COUNT = (AppiumBy.ID, f'{PACKAGE_ID}/group_member_num')
    # 加入群状态
    JOIN_GROUP_STATUS_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/group_exist_status')
    # 加入群聊和发送消息按钮
    JOIN_GROUP_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/group_add')




