from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator

class GroupBotLocator:
    """群助手功能定位器"""
    PACKAGE_ID = CommonLocator.PACKAGE_ID


    # 群详情/群管理中的入口
    GROUP_BOT_ENTRY = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("群助手")')

    # 群助手页面
    GROUP_BOT_RECYCLER_VIEW = (AppiumBy.ID, f'{PACKAGE_ID}/recycler')
    
    # 群助手功能列表入口
    KEYWORD_BLOCK_ENTRY = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("禁止发送关键词")')
    SPEECH_MANAGE_ENTRY = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("发言管理")')
    JOIN_VERIFY_ENTRY = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("进群验证")')
    AUTO_CLEAN_ENTRY = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("自动清理成员")')
    WELCOME_ENTRY = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("进群欢迎语")')
    TIMED_MSG_ENTRY = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("定时消息")')

    TV_SETTING = (AppiumBy.ID, f'{PACKAGE_ID}/tv_setting')  # 每个功能的右侧的开关状态
    
    # 共同/主页面元素
    SWITCH_BTN = (AppiumBy.CLASS_NAME, 'android.widget.Switch')
    SAVE_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("保存")')
    CONFIRM_BTN = CommonLocator.TEXT_CONFIRM_BTN
    CANCEL_BTN = CommonLocator.TEXT_CANCEL_BTN
    TV_TITLE = CommonLocator.TOP_TV_TITLE   
    IV_BACK = CommonLocator.TOP_IV_BACK_BTN

    
    # 1. 进群欢迎语页面元素
    WELCOME_ADD_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("添加欢迎语")')
    WELCOME_EDIT_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("修改欢迎语")')
    WELCOME_INPUT = (AppiumBy.CLASS_NAME, 'android.widget.EditText')
    WELCOME_FINISH_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("完成")')

    # 2. 定时消息页面元素
    ADD_TIMED_MSG_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("添加定时消息")')
    TIMED_MSG_INPUT = (AppiumBy.CLASS_NAME, 'android.widget.EditText')
    TIMED_MSG_TIME_ROW = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("设置时间")')
    TIMED_MSG_IMAGE_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("添加图片")')
    TIMED_MSG_CONFIRM_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("确认添加")')
    TIMED_MSG_SAVE_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("保存")')
    TIMED_MSG_EDIT_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("修改")')
    TIMED_MSG_DELETE_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("删除")')

    # 3. 入群验证页面元素
    VERIFY_MODE_CLICK = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("点验")')
    VERIFY_TIME_ROW = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("验证时间")')
    VERIFY_ACTION_KICK = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("仅移出群组")')
    VERIFY_ACTION_BLOCK = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("移除并拉黑")')
    VERIFY_SCOPE_ALL = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("所有新成员")')

    # 4. 禁发关键词检测页面元素
    KEYWORD_ROW = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().textContains("关键词")')
    RULE_WARN = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("警告")')
    RULE_MUTE = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("禁言")')
    RULE_KICK = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("移除群聊")')
    RULE_REVOKE = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("仅撤回")')
    RULE_BLOCK = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("自动拦截")')
    
    # 禁言时长配置
    MUTE_DURATION_ROW = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("禁言时长")')
    
    # 警告语设置
    WARNING_MSG_ROW = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().textContains("警告语")')
    ADD_WARNING_MSG_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("添加警告语")')
    
    # 关键词设置页面元素
    ADD_KEYWORD_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("新增")')
    EDIT_TEXT = (AppiumBy.CLASS_NAME, 'android.widget.EditText')
    DELETE_KEYWORD_ICON = (AppiumBy.ID, f"{PACKAGE_ID}/iv_delete")

    # 5. 发言管理页面元素
    LIMIT_TEXT_EMOJI = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("文本/emoji")')
    LIMIT_VOICE = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("语音")')
    LIMIT_EMOJI_PKG = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("表情包")')
    LIMIT_IMAGE_VIDEO = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("图片/拍照/视频")')
    LIMIT_FILE = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("文件")')
    
    # 传播与保存限制
    LIMIT_FORWARD = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("禁止转发")')
    LIMIT_COPY = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("禁止复制")')
    LIMIT_SAVE = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("禁止保存收藏")')

    # 6. 自动清理成员页面元素
    CLEAN_RULES_ENTRY = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("清理规则设置")')
    CLEAN_RECORD_ENTRY = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("任务记录")')
    
    # 清理条件勾选
    COND_NEVER_SPEAK = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("从未发言")')
    COND_NO_SPEAK_90 = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("超90天未发言")')
    COND_NO_VIEW_60 = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("超60天未查看群消息")')
    COND_BANNED = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("账号已注销或因违规被封禁")')
    
    # 保护规则勾选
    PROT_NEW_MEMBER = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("入群不足90天的成员")')
    PROT_CUSTOM = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("自定义成员")')
    
    # 清理模式
    MODE_MANUAL = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("手动确认")')
    MODE_AUTO = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("自动清理")')
    
    # 执行按钮
    FINISH_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("完成")')
    CONFIRM_CLEAN_LIST = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("确认名单")')
    CANCEL_CLEAN_TASK = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("放弃本次清理")')


    
    
    # 待验证端元素
    GO_VERIFY_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'newUiSelector().text("去验证")')










