from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator

class GroupCreateLocator(CommonLocator):
    """发起群聊页面定位器"""
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    
    FRIEND_HEADER = (AppiumBy.ID, f"{PACKAGE_ID}/friend_header")                                        # 群聊页面 群成员头像
    FRIEND_NAME = (AppiumBy.ID, f"{PACKAGE_ID}/friend_name")                                            # 群聊页面 群成员名称

    # =======================================================
    # 群聊 + 进入好友选择页面
    # =======================================================
    EDIT_TO_IV_ID = f"{PACKAGE_ID}/edit_to"
    EDIT_TO_IV = (AppiumBy.ID, EDIT_TO_IV_ID)                                           # 进入好友选择页面
    
    MEMBER_LIST_RV_ID = f"{PACKAGE_ID}/member_list_rv"
    MEMBER_LIST_RV = (AppiumBy.ID, MEMBER_LIST_RV_ID)                                    # 好友列表
    CHECK_MEMBER_ID = f"{PACKAGE_ID}/check_member"
    CHECK_MEMBER_IV = (AppiumBy.ID, CHECK_MEMBER_ID)                                     # 好友勾选框
    FRIEND_NAME_ID = f"{PACKAGE_ID}/friend_name"
    FRIEND_NAME = (AppiumBy.ID, FRIEND_NAME_ID)                                          # 好友名字

    # 好友未勾选
    UNSELECTED_CHECKBOX = (AppiumBy.XPATH, f'//*[@resource-id="{MEMBER_LIST_RV_ID}"]/android.view.ViewGroup'
                        f'//*[@resource-id="{CHECK_MEMBER_ID}" and @enabled="true"]'
                        f'/following-sibling::*[@resource-id="{FRIEND_NAME_ID}"]')
    # 有可能是系统用户
    UNSELECTED_CHECKBOX_SYSTEM_USER = (AppiumBy.XPATH, f'//*[@resource-id="{MEMBER_LIST_RV_ID}"]'
                                                        f'/android.view.ViewGroup[not(.//*[@resource-id="{FRIEND_NAME_ID}" '
                                                        f'and (@text="Abel 江湖" or @text="black")]) and .//*[@resource-id="{CHECK_MEMBER_ID}" and @enabled="true"]]'
                                                        f'//*[@resource-id="{FRIEND_NAME_ID}"]')

                        
    # 正在被选中的好友
    SELECTED_CHECKBOX = (AppiumBy.XPATH, f'//*[@resource-id="{MEMBER_LIST_RV_ID}"]/android.view.ViewGroup'
                        f'//*[@resource-id="{CHECK_MEMBER_ID}" and @enabled="false"]'
                        f'/following-sibling::*[@resource-id="{FRIEND_NAME_ID}"]')


    # =======================================================
    # 群聊页面元素
    # =======================================================
    RV_MESSAGES_ID = f"{PACKAGE_ID}/rv_messages"
    RV_MESSAGES = (AppiumBy.ID, RV_MESSAGES_ID)                                   # 消息列表

    # 群聊页面消息的类型，ex：系统消息
    MESSAGE_TEXT = (AppiumBy.XPATH, f'//*[@resource-id="{RV_MESSAGES_ID}"]//android.widget.TextView')


    INDEX_BAR_ID = f"{PACKAGE_ID}/index_bar"
    INDEX_BAR = (AppiumBy.ID, INDEX_BAR_ID)                                          # 索引栏

    # 索引栏中的文本 - 字母
    @classmethod
    def get_index_bar_text(cls, text: str):
        return (AppiumBy.XPATH, f'//*[@resource-id="{cls.INDEX_BAR_ID}"]//android.widget.TextView[@text="{text}"]')

    

    # 横幅消息元素
    TV_PREVIEW_ID = f"{PACKAGE_ID}/tv_preview"
    TV_PREVIEW = (AppiumBy.ID, TV_PREVIEW_ID)                                          # 横幅消息详细文本

