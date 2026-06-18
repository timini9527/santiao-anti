from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator

class GroupBotLocator:
    """群助手功能定位器"""
    PACKAGE_ID = CommonLocator.PACKAGE_ID


    # 群详情/群管理中的入口
    GROUP_BOT_ENTRY = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("群助手")')

    # 群助手页面
    GROUP_BOT_RECYCLER_VIEW = (AppiumBy.ID, f'{PACKAGE_ID}/recycler')
    
    # 群助手功能列表入口
    KEYWORD_BLOCK_ENTRY = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("禁止发送关键词")')
    SPEECH_MANAGE_ENTRY = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("发言管理")')
    JOIN_VERIFY_ENTRY = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("进群验证")')
    AUTO_CLEAN_ENTRY = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("自动清理成员")')
    WELCOME_ENTRY = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("进群欢迎语")')
    TIMED_MSG_ENTRY = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("定时消息")')

    TV_SETTING = (AppiumBy.ID, f'{PACKAGE_ID}/tv_setting')      # 每个功能的右侧的开关状态
    
    # 共同/主页面元素
    TV_TITLE = CommonLocator.TOP_TV_TITLE                       # 页面标题
    IV_BACK = CommonLocator.TOP_IV_BACK_BTN                     # 返回按钮
    SAVE_BTN = CommonLocator.TOP_FB_ACTION_BTN                  # 右上角保存按钮
    CONFIRM_BTN = CommonLocator.TEXT_CONFIRM_BTN                # 确认按钮
    CANCEL_BTN = CommonLocator.TEXT_CANCEL_BTN                  # 取消按钮
    SWITCH_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/switch_enable')   # 功能的开启和关闭状态的开关

    
    # 1. 进群欢迎语页面元素
    WELCOME_ADD_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("添加欢迎语")')
    WELCOME_EDIT_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("修改欢迎语")')
    WELCOME_INPUT = (AppiumBy.CLASS_NAME, 'android.widget.EditText')
    WELCOME_FINISH_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("完成")')

    # 2. 定时消息页面元素
    ADD_TIMED_MSG_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("添加定时消息")')
    TIMED_MSG_INPUT = (AppiumBy.CLASS_NAME, 'android.widget.EditText')
    TIMED_MSG_TIME_ROW = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("设置时间")')
    TIMED_MSG_IMAGE_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("添加图片")')
    TIMED_MSG_CONFIRM_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("确认添加")')
    TIMED_MSG_SAVE_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("保存")')
    TIMED_MSG_EDIT_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("修改")')
    TIMED_MSG_DELETE_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("删除")')

    # 3. 入群验证页面元素
    VERIFY_MODE_CLICK = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("点验")')
    VERIFY_TIME_ROW = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("验证时间")')
    VERIFY_ACTION_KICK = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("仅移出群组")')
    VERIFY_ACTION_BLOCK = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("移除并拉黑")')
    VERIFY_SCOPE_ALL = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("所有新成员")')

    # 4. 禁发关键词检测页面元素
    KEYWORD_ENTRY = (AppiumBy.ID, f'{PACKAGE_ID}/layout_keyword')                           # 关键词检测的入口
    KEYWORD_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_keyword_title')                         # 关键词检测的标题
    KEYWORD_SUMMARY = (AppiumBy.ID, f'{PACKAGE_ID}/tv_keyword_summary')                     # 关键词检测的状态
    
    # 添加关键词设置
    ADD_KEYWORD_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("新增")')       # 添加关键词按钮
    ET_KEYWORD_INPUT = (AppiumBy.ID, f'{PACKAGE_ID}/et_keyword_input')                      # 关键词输入框
    TV_KEYWORD_NUMBER = (AppiumBy.ID, f'{PACKAGE_ID}/tv_keyword')                           # 关键词
    DELETE_KEYWORD_ICON = (AppiumBy.ID, f'{PACKAGE_ID}/iv_delete')                          # 删除关键词图标
    TV_SAVE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_save')                                        # 保存按钮
    
    # 删除关键词二次确认框
    MESSAGE_BOX = (AppiumBy.ID, f'{PACKAGE_ID}/message')                                # 二次确认框
    TITLE = TV_TITLE                                                                    # 确认/取消对话框的标题
    NEGATIVE_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/negativeButton')                     # 确认按钮
    POSITIVE_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/positiveButton')                     # 取消按钮

    
    # 关键词处理方式
    DESIGN_BOTTOM_SHEET = (AppiumBy.ID, f'{PACKAGE_ID}/design_bottom_sheet')                # bottomSheet 警告语布局
    RULE_REVOKE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("仅撤回")')          # 仅撤回
    RULE_WARN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("撤回+公开警告")')     # 撤回+公开警告
    
    RULE_MUTE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("撤回+禁言")')         # 撤回+禁言
    TV_SUMMARY = (AppiumBy.ID, f'{PACKAGE_ID}/tv_summary')                                  # 设置禁言时长
    PICKER_DURATION = (AppiumBy.ID, f'{PACKAGE_ID}/picker_duration')                        # 设置禁言时长控件
    
    RULE_KICK = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("撤回+移除群聊")')     # 撤回+移除群聊
    
    # 警告语设置
    TV_CONTENT = (AppiumBy.ID, f'{PACKAGE_ID}/tv_content')                                  # 警告语默认内容
    TV_CUSTOM = (AppiumBy.ID, f'{PACKAGE_ID}/tv_custom')                                    # 自定义
    TV_EDIT = (AppiumBy.ID, f'{PACKAGE_ID}/tv_edit')                                        # 编辑按钮
    ET_WARNING_MSG = (AppiumBy.ID, f'{PACKAGE_ID}/et_warning')                              # 警告语输入框
    BTN_CONFIRM = (AppiumBy.ID, f'{PACKAGE_ID}/btn_confirm')                                # 确认按钮
    BTN_CANCEL = (AppiumBy.ID, f'{PACKAGE_ID}/btn_cancel')                                  # 取消按钮
    
    # 禁言时长配置
    MUTE_DURATION_ROW = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("禁言时长")')
    
    # 警告语设置
    WARNING_MSG_ROW = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("警告语")')
    ADD_WARNING_MSG_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("添加警告语")')
    

    # 5. 发言管理
    # 整个页面容器
    ACTION_BAR_ROOT = (AppiumBy.ID, f'{PACKAGE_ID}/action_bar_root')                    
    FRAGMENT_CONTAINER_VIEW = (AppiumBy.ID, f'{PACKAGE_ID}/fragment_container_view')

    TV_STATUS = (AppiumBy.ID, f'{PACKAGE_ID}/tv_status')        # 发言管理
    SB_STATUS = (AppiumBy.ID, f'{PACKAGE_ID}/sb_status')        # 发言管理总开关
    
    SB_OPTION_ID = f'{PACKAGE_ID}/sb_option'                    # 发言管理各功能的switch开关
    SB_OPTION = (AppiumBy.ID, SB_OPTION_ID)

    # 动态匹配switch的xpath
    @staticmethod
    def SB_OPTION_BY_STATUS(checked: bool) -> tuple:
        """通过开关的状态进行查询的xpath（获取对应状态的 switch 元素）"""
        status_str = "true" if checked else "false"
        return (AppiumBy.XPATH, f'//*[@resource-id="{SB_OPTION_ID}" and @checked="{status_str}"]')

    # 动态匹配文本标题的xpath
    @classmethod
    def TV_TITLE_BY_SWITCH_STATUS(cls, checked: bool) -> tuple:
        """通过开关的状态进行查询的xpath（获取对应状态的文本标题元素）"""
        status_str = "true" if checked else "false"
        return (AppiumBy.XPATH, f'//*[@resource-id="{cls.SB_OPTION_ID}" and @checked="{status_str}"]/preceding-sibling::*[@resource-id="{cls.TV_TITLE}"]')
    

    # 6. 自动清理成员页面元素
    CLEAN_RULES_ENTRY = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("清理规则设置")')
    CLEAN_RECORD_ENTRY = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("任务记录")')
    
    # 清理条件勾选
    COND_NEVER_SPEAK = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("从未发言")')
    COND_NO_SPEAK_90 = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("超90天未发言")')
    COND_NO_VIEW_60 = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("超60天未查看群消息")')
    COND_BANNED = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("账号已注销或因违规被封禁")')
    
    # 保护规则勾选
    PROT_NEW_MEMBER = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("入群不足90天的成员")')
    PROT_CUSTOM = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("自定义成员")')
    
    # 清理模式
    MODE_MANUAL = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("手动确认")')
    MODE_AUTO = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("自动清理")')
    
    # 执行按钮
    FINISH_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("完成")')
    CONFIRM_CLEAN_LIST = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("确认名单")')
    CANCEL_CLEAN_TASK = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("放弃本次清理")')


    
    
    # 待验证端元素
    GO_VERIFY_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("去验证")')










