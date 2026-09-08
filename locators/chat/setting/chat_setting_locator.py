from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator

class ChatSettingLocator(CommonLocator):
    """单聊设置页面（聊天信息）定位器"""
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 聊天对象信息
    SETTING_FRIEND_AVATAR = (AppiumBy.ID, f'{PACKAGE_ID}/setting_friend_header')        # 聊天对象头像
    SETTING_FRIEND_NAME = (AppiumBy.ID, f'{PACKAGE_ID}/setting_friend_name')            # 聊天对象昵称
    SETTING_ADD_FRIEND = (AppiumBy.ID, f'{PACKAGE_ID}/setting_friend_add')              # 添加更多朋友（建群）

    # 查找聊天记录
    SEARCH_CHAT_RECORD = (AppiumBy.ID, f'{PACKAGE_ID}/setting_search_ChatMessage')      # 查找聊天记录
    SEARCH_CHAT_RECORD_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("查找聊天记录")') # 查找聊天记录文本

    # 通用开关按钮
    SWITCH_BTN_ID = f'{PACKAGE_ID}/switch_btn'
    SWITCH_BTN = (AppiumBy.ID, SWITCH_BTN_ID)                                           # 切换按钮

    # 置顶聊天（私聊使用 CheckBox 开关）
    SETTING_TOP_CHAT = (AppiumBy.ID, f'{PACKAGE_ID}/setting_chat_setTop')               
    SETTING_TOP_CHAT_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("置顶聊天")')
    SETTING_TOP_CHAT_BTN = (AppiumBy.XPATH, "//*[@text='置顶聊天']/following-sibling::android.widget.CheckBox") # 置顶聊天按钮

    # 群聊快捷置顶与搜索记录（群聊使用 LinearLayout 块，置顶后文本由"置顶聊天"变成"取消置顶"）
    GROUP_QUICK_SEARCH = (AppiumBy.ID, f'{PACKAGE_ID}/quick_search')                                            # 群聊快捷搜索记录
    GROUP_QUICK_PIN = (AppiumBy.ID, f'{PACKAGE_ID}/quick_pin')                                                  # 群聊快捷置顶块
    GROUP_QUICK_PIN_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/quick_pin_text')                                        # 群聊快捷置顶文本

    # 消息免打扰
    SETTING_CHAT_REMIND = (AppiumBy.ID, f'{PACKAGE_ID}/setting_chat_dnd')               
    SETTING_CHAT_REMIND_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("消息免打扰")')
    SETTING_CHAT_REMIND_BTN = (AppiumBy.XPATH, "//*[@text='消息免打扰']/following-sibling::android.widget.CheckBox") # 消息免打扰按钮

    # 聊天密码
    SETTING_CHAT_PWD = (AppiumBy.ID, f'{PACKAGE_ID}/setting_chat_pwd')                   
    SETTING_CHAT_PWD_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("聊天密码")')
    SETTING_CHAT_PWD_BTN = (AppiumBy.XPATH, "//*[@text='聊天密码']/following-sibling::android.widget.CheckBox") # 聊天密码按钮

    # 截屏通知
    SETTING_CHAT_SCREEN_SHOT = (AppiumBy.ID, f'{PACKAGE_ID}/setting_chat_screenshot_notification') 
    SETTING_CHAT_SCREEN_SHOT_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("截屏通知")')
    SETTING_CHAT_SCREEN_SHOT_BTN = (AppiumBy.XPATH, "//*[@text='截屏通知']/following-sibling::android.widget.CheckBox") # 截屏通知按钮

    # 撤回通知
    SETTING_CHAT_REVOKE = (AppiumBy.ID, f'{PACKAGE_ID}/setting_chat_revoke_notification')   
    SETTING_CHAT_REVOKE_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("撤回通知")')
    SETTING_CHAT_REVOKE_BTN = (AppiumBy.XPATH, "//*[@text='撤回通知']/following-sibling::android.widget.CheckBox") # 撤回通知按钮

    # 投诉与清空
    SETTING_CHAT_REPORT = (AppiumBy.ID, f'{PACKAGE_ID}/setting_report')                     
    SETTING_CHAT_REPORT_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("投诉")')

    SETTING_CHAT_CLEAR = (AppiumBy.ID, f'{PACKAGE_ID}/setting_clear_chatMessage')            
    SETTING_CHAT_CLEAR_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("清空聊天记录")')

    # 二次确认清空聊天记录
    TWO_CONFIRM = CommonLocator.TV_CONFIRM_BTN
    TWO_CANCEL = CommonLocator.TV_CANCEL_BTN


    # 投诉页面
    









