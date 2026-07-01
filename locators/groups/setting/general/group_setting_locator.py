from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator
from locators.chat.chat_setting_locator import ChatSettingLocator


class GroupSettingLocator(ChatSettingLocator):
    """群聊设置/群管理页面定位器"""

    PACKAGE_ID = CommonLocator.PACKAGE_ID

    TV_TITLE = CommonLocator.TOPBAR_TITLE
    BACK = CommonLocator.TOPBAR_LEFT_BACK_BTN

    # 成员区域
    FRIEND_HEADER_ID = f"{PACKAGE_ID}/friend_header"                                                    # 群成员头像 ID
    FRIEND_HEADER = (AppiumBy.ID, FRIEND_HEADER_ID)                                                     # 群成员头像
    FRIEND_NAME_ID = f"{PACKAGE_ID}/friend_name"                                                        # 群成员名称 ID
    FRIEND_NAME = (AppiumBy.ID, FRIEND_NAME_ID)                                                         # 群成员名称
    
    # 基础信息设置项
    SETTING_CHAT_GROUP_CODE = (AppiumBy.ID, f"{PACKAGE_ID}/setting_chat_groupCode")                     # 群聊二维码
    SETTING_CHAT_GROUP_ANNOUNCEMENT = (AppiumBy.ID, f"{PACKAGE_ID}/setting_chat_groupAnnouncement")     # 群公告
    SETTING_CHAT_GROUP_REMARKS_ID = f"{PACKAGE_ID}/setting_chat_groupRemarks"                           # 群备注 ID
    SETTING_CHAT_GROUP_REMARKS = (AppiumBy.ID, f"{SETTING_CHAT_GROUP_REMARKS_ID}")                      # 群备注
    SETTING_CHAT_GROUP_MANAGER = (AppiumBy.ID, f"{PACKAGE_ID}/setting_chat_groupManager")               # 群管理
    SETTING_CHAT_GROUP_HEADER = (AppiumBy.ID, f"{PACKAGE_ID}/setting_chat_groupHeader")                 # 群头像
    SETTING_CHAT_GROUP_NAME_ID = f"{PACKAGE_ID}/setting_chat_groupName"                                 # 群聊名称ID
    SETTING_CHAT_GROUP_NAME = (AppiumBy.ID, f"{SETTING_CHAT_GROUP_NAME_ID}")                            # 群聊名称
    SETTING_SEARCH_GROUPCHATMESSAGE = (AppiumBy.ID, f"{PACKAGE_ID}/setting_search_groupChatMessage")    # 查找聊天记录
    
    # 其他设置项
    SETTING_CHAT_DND = ChatSettingLocator.SETTING_CHAT_REMIND                                           # 免打扰
    SETTING_CHAT_SETTOP = ChatSettingLocator.SETTING_TOP_CHAT                                           # 置顶聊天
    SETTING_CHAT_PWD = ChatSettingLocator.SETTING_CHAT_PWD                                              # 聊天密码
    SETTING_CHAT_NAME_FORME = (AppiumBy.ID, f"{PACKAGE_ID}/setting_chat_name_forMe")                    # 设置群聊名称(针对自己)
    SETTING_CHAT_SHOW_MEMBER_NAME = (AppiumBy.ID, f"{PACKAGE_ID}/setting_chat_showMemberName")          # 显示群成员昵称
    
    # 精确的 Switch 开关定位器
    SETTING_CHAT_DND_SWITCH = (AppiumBy.XPATH, "//*[contains(@resource-id, 'setting_chat_dnd')]//*[contains(@resource-id, 'switch_btn')]")
    SETTING_CHAT_SETTOP_SWITCH = (AppiumBy.XPATH, "//*[contains(@resource-id, 'setting_chat_setTop')]//*[contains(@resource-id, 'switch_btn')]")
    SETTING_CHAT_PWD_SWITCH = (AppiumBy.XPATH, "//*[contains(@resource-id, 'setting_chat_pwd')]//*[contains(@resource-id, 'switch_btn')]")
    SETTING_CHAT_SHOW_MEMBER_NAME_SWITCH = (AppiumBy.XPATH, "//*[contains(@resource-id, 'setting_chat_showMemberName')]//*[contains(@resource-id, 'switch_btn')]")

    
    # 底部危险操作
    SETTING_CLEAR_GROUPCHATMESSAGE = (AppiumBy.ID, f"{PACKAGE_ID}/setting_clear_groupChatMessage")      # 清空聊天记录
    SETTING_GROUP_DELETE_AND_OUT = (AppiumBy.ID, f"{PACKAGE_ID}/setting_chat_groupDeleteAndOut")        # 删除并退出

    # 通用弹窗-二次确认
    TV_CONFIRM = CommonLocator.TEXT_CONFIRM_BTN                                                          # 确认按钮
    TV_CANCEL = CommonLocator.TEXT_CANCEL_BTN                                                            # 取消按钮 

    # 群备注弹窗
    # 群备注名称
    NVA_TV_REMARK = (AppiumBy.XPATH, f"//*[contains(@resource-id, '{SETTING_CHAT_GROUP_REMARKS_ID}')]//*[contains(@resource-id, 'nva_tv')]") 
    REMARK_DIALOG_TITLE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_main")                                        # 弹窗标题
    REMARK_DIALOG_INPUT = (AppiumBy.ID, f"{PACKAGE_ID}/update_name")                                    # 输入框 


    # 群头像-弹窗相关
    ACTION_TAKE_PHOTO = (AppiumBy.ID, f"{PACKAGE_ID}/action_take_photo")                                # 拍照
    ACTION_PICK_GALLERY = (AppiumBy.ID, f"{PACKAGE_ID}/action_pick_gallery")                            # 从相册选择
    ACTION_SAVE_IMAGE = (AppiumBy.ID, f"{PACKAGE_ID}/action_save_image")                                # 保存图片
    ACTION_CANCEL = (AppiumBy.ID, f"{PACKAGE_ID}/action_cancel")                                        # 取消按钮
    
    # 群名称：
    TV_MESSAGE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_message")                                              # 无权限弹窗内容提示
    TV_SECOND = (AppiumBy.ID, f"{PACKAGE_ID}/tv_second")                                                # 修改群公告弹窗内容提示
    # 群聊设置页面群聊名称
    NVA_TV_NAME = (AppiumBy.XPATH, f"//*[contains(@resource-id, '{SETTING_CHAT_GROUP_NAME_ID}')]//*[contains(@resource-id, 'nva_tv')]")


    # @所有人按钮
    LL_AT_ALL = (AppiumBy.ID, f"{PACKAGE_ID}/ll_at_all")                                                # @所有人按钮

    
    # 群成员-通过成员名称定位其头像
    @classmethod
    def get_member_avatar_by_name(cls, name: str) -> tuple:
        """通过成员名称定位其头像"""
        return (AppiumBy.XPATH, f"//*[@resource-id='{cls.FRIEND_NAME_ID}' and contains(@text, '{name}')]/preceding-sibling::*[@resource-id='{cls.FRIEND_HEADER_ID}']")
