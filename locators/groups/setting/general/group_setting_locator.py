from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator
from locators.chat.setting.chat_setting_locator import ChatSettingLocator


class GroupSettingLocator(ChatSettingLocator):
    """新版群聊设置/群详情页面定位器"""

    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # =========================================================================
    # 1. 顶部导航栏
    # =========================================================================
    TV_TITLE = CommonLocator.TOP_BAR_TITLE_TV                                                           # 标题 ("群详情")
    BACK = CommonLocator.TOP_BAR_BACK_BTN                                                               # 返回按钮
    IV_BACK_BUTTON = CommonLocator.TOP_IV_BACK_BTN                                                      # 返回按钮
    TOP_GROUP_CODE = (AppiumBy.ID, f"{PACKAGE_ID}/top_group_code")                                      # 顶部群二维码
    TOP_GROUP_SHARE = (AppiumBy.ID, f"{PACKAGE_ID}/top_group_share")                                    # 顶部群分享

    # =========================================================================
    # 2. 成员区域
    # =========================================================================
    MEMBER_LIST = (AppiumBy.ID, "member_list")                                                          # 成员列表容器
    FRIEND_HEADER_ID = f"{PACKAGE_ID}/friend_header"                                                    # 群成员头像 ID
    FRIEND_HEADER = (AppiumBy.ID, FRIEND_HEADER_ID)                                                     # 群成员头像
    FRIEND_NAME_ID = f"{PACKAGE_ID}/friend_name"                                                        # 群成员名称 ID
    FRIEND_NAME = (AppiumBy.ID, FRIEND_NAME_ID)                                                         # 群成员名称

    # =========================================================================
    # 3. 基础信息设置项
    # =========================================================================
    GROUP_HEADER = (AppiumBy.ID, f"{PACKAGE_ID}/group_avatar_header")                                   # 群头像
    GROUP_NAME_ROW = (AppiumBy.ID, f"{PACKAGE_ID}/group_name_row")                                      # 群聊名称容器/行
    GROUP_NAME_HEADER = (AppiumBy.ID, f"{PACKAGE_ID}/group_name_header")                                # 群聊名称文本
    GROUP_REMARK_ROW = (AppiumBy.ID, f"{PACKAGE_ID}/group_remark_row")                                  # 群备注容器/行
    GROUP_REMARK_HEADER = (AppiumBy.ID, f"{PACKAGE_ID}/group_remark_header")                            # 群备注文本

    # =========================================================================
    # 4. 快捷操作区域 (Quick Actions)
    # =========================================================================
    GROUP_QUICK_SEARCH = (AppiumBy.ID, f"{PACKAGE_ID}/quick_search")                                    # 查找聊天记录 / 搜索记录
    GROUP_QUICK_PIN = (AppiumBy.ID, f"{PACKAGE_ID}/quick_pin")                                          # 置顶聊天
    GROUP_QUICK_PIN_TEXT = (AppiumBy.ID, f"{PACKAGE_ID}/quick_pin_text")                                # 置顶聊天状态文本（未置顶："置顶聊天"，已置顶："取消置顶"）
    GROUP_QUICK_MANAGE = (AppiumBy.ID, f"{PACKAGE_ID}/quick_manage")                                    # 群管理
    GROUP_QUICK_MORE = (AppiumBy.ID, f"{PACKAGE_ID}/quick_more")                                        # 更多操作菜单

    # =========================================================================
    # 5. 更多操作弹出项 (More Options)
    # =========================================================================
    GROUP_MORE_CLEAR_CHAT = (AppiumBy.ID, f"{PACKAGE_ID}/group_more_clear_chat")                        # 清空聊天记录
    GROUP_MORE_DELETE_EXIT = (AppiumBy.ID, f"{PACKAGE_ID}/group_more_delete_exit")                      # 删除并退出
    GROUP_MORE_REPORT = (AppiumBy.ID, f"{PACKAGE_ID}/group_more_report")                                # 举报群聊

    # =========================================================================
    # 6. 公告与活跃度卡片
    # =========================================================================
    GROUP_ANNOUNCEMENT_CARD = (AppiumBy.ID, f"{PACKAGE_ID}/announcement_card")                          # 群公告容器
    GROUP_ANNOUNCEMENT_TITLE = (AppiumBy.ID, f"{PACKAGE_ID}/group_announcement_title")                  # 群公告标题/文本
    GROUP_ACTIVE_CARD = (AppiumBy.ID, f"{PACKAGE_ID}/group_active_card")                                # 群活跃度容器
    GROUP_ACTIVE_VALUE = (AppiumBy.ID, f"{PACKAGE_ID}/group_active_value")                              # 群活跃度值

    # =========================================================================
    # 7. 开关设置项 (Switches)
    # =========================================================================
    GROUP_DND_TITLE_TV = (AppiumBy.ID, f"{PACKAGE_ID}/group_dnd_title_tv")                              # 消息免打扰标题
    GROUP_DND_SWITCH_BTN = (AppiumBy.ID, f"{PACKAGE_ID}/group_dnd_switch_btn")                          # 消息免打扰开关
    GROUP_PWD_TITLE_TV = (AppiumBy.ID, f"{PACKAGE_ID}/group_pwd_title_tv")                              # 聊天密码标题
    GROUP_PWD_SWITCH_BTN = (AppiumBy.ID, f"{PACKAGE_ID}/group_pwd_switch_btn")                          # 聊天密码开关

    GROUP_NAME_FORME_TITLE_TV = (AppiumBy.ID, f"{PACKAGE_ID}/setting_chat_name_forMe")                  # 我在本群昵称容器
    GROUP_NAME_FORME_SWITCH_BTN = (AppiumBy.ID, f"{PACKAGE_ID}/setting_chat_name_forMe_title_tv")       # 我在本群昵称标题
    GROUP_NAME_FORME_NVA_TV = (AppiumBy.ID, f"{PACKAGE_ID}/setting_chat_name_forMe_nva_tv")             # 我在本群昵称展示值
    
    GROUP_SHOW_MEMBER_NAME_TITLE_TV = (AppiumBy.ID, f"{PACKAGE_ID}/setting_chat_showMemberName_title_tv")       # 显示群成员昵称标题
    GROUP_SHOW_MEMBER_NAME_SWITCH_BTN = (AppiumBy.ID, f"{PACKAGE_ID}/setting_chat_showMemberName_switch_btn")   # 显示群成员昵称开关

    # =========================================================================
    # 8. 通用确认/取消弹窗
    # =========================================================================
    TV_CONFIRM = CommonLocator.TV_CONFIRM_BTN                                                           # 确认按钮
    TV_CANCEL = CommonLocator.TV_CANCEL_BTN                                                             # 取消按钮 

    # =========================================================================
    # 9. 群备注弹窗相关
    # =========================================================================
    REMARK_DIALOG_TITLE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_main")                                        # 弹窗标题
    REMARK_DIALOG_INPUT = (AppiumBy.ID, f"{PACKAGE_ID}/update_name")                                    # 输入框 

    # =========================================================================
    # 10. 群头像弹窗相关
    # =========================================================================
    ACTION_TAKE_PHOTO = (AppiumBy.ID, f"{PACKAGE_ID}/action_take_photo")                                # 拍照
    ACTION_PICK_GALLERY = (AppiumBy.ID, f"{PACKAGE_ID}/action_pick_gallery")                            # 从相册选择
    ACTION_SAVE_IMAGE = (AppiumBy.ID, f"{PACKAGE_ID}/action_save_image")                                # 保存图片
    ACTION_CANCEL = (AppiumBy.ID, f"{PACKAGE_ID}/action_cancel")                                        # 取消按钮
    
    # =========================================================================
    # 11. 权限提示与群公告编辑弹窗
    # =========================================================================
    TV_MESSAGE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_message")                                              # 无权限弹窗内容提示
    TV_SECOND = (AppiumBy.ID, f"{PACKAGE_ID}/tv_second")                                                # 修改群公告弹窗内容提示
    LL_AT_ALL = (AppiumBy.ID, f"{PACKAGE_ID}/ll_at_all")                                                # @所有人按钮

    # =========================================================================
    # 12. 动态定位器
    # =========================================================================
    @classmethod
    def get_member_avatar_by_name(cls, name: str) -> tuple:
        """通过成员名称定位其头像"""
        return (AppiumBy.XPATH, f"//*[@resource-id='{cls.FRIEND_NAME_ID}' and contains(@text, '{name}')]/preceding-sibling::*[@resource-id='{cls.FRIEND_HEADER_ID}']")

