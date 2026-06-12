import time
from core.logger_utils import logger
from common.base_page import BasePage
from appium.webdriver.common.appiumby import AppiumBy
from locators.groups.bot.group_bot_locator import GroupBotLocator



class GroupBotPage(BasePage):
    """群助手页面操作类，涵盖禁发关键词、发言管理、自动清理、入群验证、入群欢迎语、定时消息、自动清理群成员等功能域"""

    # ==========================
    # 页面进入与基本导航
    # ==========================

    # 从群详情/群管理页进入群助手页面
    def wait_for_group_bot_page_load(self, timeout=10) -> bool:
        """从群详情/群管理页进入群助手页面"""
        bot_list = self.find_elements(GroupBotLocator.GROUP_BOT_RECYCLER_VIEW, timeout=timeout)
        if not bot_list:
            logger.error(f"❌ [Action-GroupBotPage] 未找到群助手功能页面,等待超时 {timeout} 秒")
            raise Exception("未找到群助手功能页面")
        logger.info(f"✅ [Action-GroupBotPage] 成功进入【群助手功能页面】,共找到 {len(bot_list)} 个群助手功能")
        return True

    # 进入【禁发关键词检测】设置页面
    def enter_keyword_block(self):
        """进入【禁发关键词检测】设置页面"""
        logger.info("⏳ [Action-GroupBotPage] 进入【禁发关键词检测】设置页")
        self.click(GroupBotLocator.KEYWORD_BLOCK_ENTRY)
        time.sleep(1)

    # 进入【发言管理】设置页面
    def enter_speech_manage(self):
        """进入【发言管理】设置页面"""
        logger.info("⏳ [Action-GroupBotPage] 进入【发言管理】设置页")
        self.click(GroupBotLocator.SPEECH_MANAGE_ENTRY)
        time.sleep(1)

    # 进入【自动清理成员】设置页面
    def enter_auto_clean(self):
        """进入【自动清理成员】页面"""
        logger.info("⏳ [Action-GroupBotPage] 进入【自动清理成员】页")
        self.click(GroupBotLocator.AUTO_CLEAN_ENTRY)
        time.sleep(1)

    # 进入【入群验证】设置页面
    def enter_join_verify(self):
        """进入【入群验证】设置页面"""
        logger.info("⏳ [Action-GroupBotPage] 进入【入群验证】设置页")
        self.click(GroupBotLocator.JOIN_VERIFY_ENTRY)
        time.sleep(1)

    # ==========================
    # 通用开关与保存/确认操作
    # ==========================
    
    # 获取当前页面主功能的 Switch 开关状态
    def get_switch_state(self) -> bool:
        """获取当前页面主功能的 Switch 开关状态"""
        checked = self.get_attribute(GroupBotLocator.SWITCH_BTN, "checked")
        state = str(checked).lower() == 'true'
        logger.info(f"⚙️ [Action-GroupBotPage] 获取 Switch 开关状态: {state}")
        return state

    # 切换主功能 Switch 开关状态
    def toggle_switch(self, enable: bool):
        """切换主功能 Switch 开关状态"""
        current_state = self.get_switch_state()
        if current_state != enable:
            logger.info(f"⚙️ [Action-GroupBotPage] 切换 Switch 开关状态 -> {enable}")
            self.click(GroupBotLocator.SWITCH_BTN)
            time.sleep(1)
        else:
            logger.info(f"⚙️ [Action-GroupBotPage] 开关状态已为 {enable}，无需切换")

    # 点击右上角保存
    def click_save(self):
        """点击右上角保存"""
        logger.info("⚙️ [Action-GroupBotPage] 点击【保存】")
        self.click(GroupBotLocator.SAVE_BTN)
        time.sleep(1)

    # 点击弹窗确认按钮
    def click_confirm(self):
        """点击弹窗确认按钮"""
        logger.info("⚙️ [Action-GroupBotPage] 点击弹窗【确认】")
        self.click(GroupBotLocator.CONFIRM_BTN)
        time.sleep(1)

    # 点击弹窗取消按钮
    def click_cancel(self):
        """点击弹窗取消按钮"""
        logger.info("⚙️ [Action-GroupBotPage] 点击弹窗【取消】")
        self.click(GroupBotLocator.CANCEL_BTN)
        time.sleep(0.5)

    # ==========================
    # 禁发关键词检测页面细化操作
    # ==========================

    # 点击关键词行进入关键词列表配置页
    def click_keyword_row(self):
        """点击关键词行进入关键词列表配置页"""
        logger.info("⚙️ [Action-GroupBotPage] 点击进入【关键词】配置列表")
        self.click(GroupBotLocator.KEYWORD_ROW)
        time.sleep(1)

    # 清空并设置新的关键词列表
    def set_keywords(self, keywords: list[str]):
        """清空并设置新的关键词列表"""
        logger.info(f"⚙️ [Action-GroupBotPage] 准备配置关键词列表: {keywords}")
        
        # 1. 尝试清空已有的输入框
        # 不断查找删除图标并点击，直到只剩一个或清空
        while True:
            try:
                delete_icons = self.find_elements(GroupBotLocator.DELETE_KEYWORD_ICON, timeout=1)
                if not delete_icons:
                    break
                logger.info("⚙️ [Action-GroupBotPage] 发现已有关键词，进行删除操作")
                self.click(delete_icons[0])
                self.click_confirm()
                time.sleep(0.5)
            except Exception:
                break

        # 2. 逐一输入新的关键词
        for i, kw in enumerate(keywords):
            edit_fields = self.find_elements(GroupBotLocator.EDIT_TEXT, timeout=2)
            if not edit_fields:
                logger.error("❌ [Action-GroupBotPage] 未找到关键词输入框")
                raise Exception("未找到关键词输入框")
            
            # 始终在最后一个输入框输入
            last_field = edit_fields[-1]
            last_field.clear()
            last_field.send_keys(kw)
            logger.info(f"⚙️ [Action-GroupBotPage] 在第 {len(edit_fields)} 个输入框中输入关键词: {kw}")
            
            # 如果不是最后一个关键词，点击新增
            if i < len(keywords) - 1:
                logger.info("⚙️ [Action-GroupBotPage] 点击右上角【新增】关键词输入框")
                self.click(GroupBotLocator.ADD_KEYWORD_BTN)
                time.sleep(0.5)

        # 3. 点击保存
        self.click_save()

    # 选择处置规则: 警告、禁言、移除群聊、仅撤回、自动拦截
    def select_action_rule(self, rule_name: str):
        """选择处置规则: 警告、禁言、移除群聊、仅撤回、自动拦截"""
        logger.info(f"⚙️ [Action-GroupBotPage] 选择处置规则: {rule_name}")
        if rule_name == "警告":
            self.click(GroupBotLocator.RULE_WARN)
        elif rule_name == "禁言":
            self.click(GroupBotLocator.RULE_MUTE)
        elif rule_name == "移除群聊":
            self.click(GroupBotLocator.RULE_KICK)
        elif rule_name == "仅撤回":
            self.click(GroupBotLocator.RULE_REVOKE)
        elif rule_name == "自动拦截":
            self.click(GroupBotLocator.RULE_BLOCK)
        else:
            raise ValueError(f"不支持的处置规则: {rule_name}")
        time.sleep(0.5)

    # 如果选择了禁言，设置禁言时长
    def select_mute_duration(self, duration: str):
        """如果选择了禁言，设置禁言时长 (例如 '10分钟', '30分钟', '永久禁言')"""
        logger.info(f"⚙️ [Action-GroupBotPage] 正在设置禁言时长为: {duration}")
        self.click(GroupBotLocator.MUTE_DURATION_ROW)
        time.sleep(1)
        duration_option = (AppiumBy.ANDROID_UIAUTOMATOR, f'newUiSelector().text("{duration}")')
        self.click(duration_option)
        time.sleep(0.5)

    # 点击警告语行进入警告语列表页
    def click_warning_msg_row(self):
        """点击警告语行进入警告语列表页"""
        logger.info("⚙️ [Action-GroupBotPage] 点击进入【警告语】配置列表")
        self.click(GroupBotLocator.WARNING_MSG_ROW)
        time.sleep(1)

    # 在列表中选择一条警告语（通过模糊文本匹配）
    def select_warning_msg(self, msg_pattern: str):
        """在列表中选择一条警告语（通过模糊文本匹配）"""
        logger.info(f"⚙️ [Action-GroupBotPage] 选择包含特定文案的警告语: {msg_pattern}")
        target_locator = (AppiumBy.ANDROID_UIAUTOMATOR, f'newUiSelector().textContains("{msg_pattern}")')
        self.click(target_locator)
        time.sleep(0.5)
        # 点击确定保存回显
        self.click(GroupBotLocator.SAVE_BTN)
        time.sleep(1)

    # 添加自定义警告语
    def add_custom_warning_msg(self, content: str):
        """添加自定义警告语"""
        logger.info(f"⚙️ [Action-GroupBotPage] 正在添加自定义警告语: {content}")
        self.click(GroupBotLocator.ADD_WARNING_MSG_BTN)
        time.sleep(1)
        edit_fields = self.find_elements(GroupBotLocator.EDIT_TEXT, timeout=2)
        if edit_fields:
            edit_fields[0].send_keys(content)
            self.click_save()
            time.sleep(1)
        else:
            logger.error("❌ [Action-GroupBotPage] 添加自定义警告语时未找到输入框")

    # ==========================
    # 发言管理页面细化操作
    # ==========================

    # 对指定的限制类型或传播限制进行勾选/取消勾选
    def toggle_limit_item(self, item_name: str, enable: bool):
        """对指定的限制类型或传播限制进行勾选/取消勾选"""
        logger.info(f"⚙️ [Action-GroupBotPage] 设置限制项【{item_name}】状态为: {enable}")
        
        # 匹配元素定位器
        locators_map = {
            "文本/emoji": GroupBotLocator.LIMIT_TEXT_EMOJI,
            "语音": GroupBotLocator.LIMIT_VOICE,
            "表情包": GroupBotLocator.LIMIT_EMOJI_PKG,
            "图片/拍照/视频": GroupBotLocator.LIMIT_IMAGE_VIDEO,
            "文件": GroupBotLocator.LIMIT_FILE,
            "禁止转发": GroupBotLocator.LIMIT_FORWARD,
            "禁止复制": GroupBotLocator.LIMIT_COPY,
            "禁止保存收藏": GroupBotLocator.LIMIT_SAVE
        }
        
        if item_name not in locators_map:
            raise ValueError(f"未知的限制项: {item_name}")
            
        locator = locators_map[item_name]
        
        # 获取其勾选状态，通常 checked 属性在对应元素或者其父布局上
        is_checked = self.get_attribute(locator, "checked")
        state = str(is_checked).lower() == 'true'
        
        if state != enable:
            self.click(locator)
            time.sleep(0.5)
        else:
            logger.info(f"⚙️ [Action-GroupBotPage] 限制项【{item_name}】状态已为 {enable}，无需点击")

    # ==========================
    # 自动清理成员页面细化操作
    # ==========================

    # 进入清理规则设置页面
    def enter_clean_rules(self):
        """进入清理规则设置页面"""
        logger.info("⚙️ [Action-GroupBotPage] 点击进入【清理规则设置】")
        self.click(GroupBotLocator.CLEAN_RULES_ENTRY)
        time.sleep(1)

    # 配置清理条件
    def toggle_clean_condition(self, cond_name: str, enable: bool):
        """配置清理条件"""
        logger.info(f"⚙️ [Action-GroupBotPage] 设置清理条件【{cond_name}】状态为: {enable}")
        locators_map = {
            "从未发言": GroupBotLocator.COND_NEVER_SPEAK,
            "超90天未发言": GroupBotLocator.COND_NO_SPEAK_90,
            "超60天未查看群消息": GroupBotLocator.COND_NO_VIEW_60,
            "账号已注销或因违规被封禁": GroupBotLocator.COND_BANNED
        }
        if cond_name not in locators_map:
            raise ValueError(f"未知的清理条件: {cond_name}")
            
        locator = locators_map[cond_name]
        is_checked = self.get_attribute(locator, "checked")
        state = str(is_checked).lower() == 'true'
        
        if state != enable:
            self.click(locator)
            time.sleep(0.5)

    # 配置保护规则
    def toggle_protect_rule(self, prot_name: str, enable: bool):
        """配置保护规则"""
        logger.info(f"⚙️ [Action-GroupBotPage] 设置保护规则【{prot_name}】状态为: {enable}")
        locators_map = {
            "入群不足90天的成员": GroupBotLocator.PROT_NEW_MEMBER,
            "自定义成员": GroupBotLocator.PROT_CUSTOM
        }
        if prot_name not in locators_map:
            raise ValueError(f"未知的保护规则: {prot_name}")
            
        locator = locators_map[prot_name]
        is_checked = self.get_attribute(locator, "checked")
        state = str(is_checked).lower() == 'true'
        
        if state != enable:
            self.click(locator)
            time.sleep(0.5)

    # 选择清理模式: 手动确认、自动清理
    def select_clean_mode(self, mode_name: str):
        """选择清理模式: 手动确认、自动清理"""
        logger.info(f"⚙️ [Action-GroupBotPage] 选择清理模式为: {mode_name}")
        if mode_name == "手动确认":
            self.click(GroupBotLocator.MODE_MANUAL)
        elif mode_name == "自动清理":
            self.click(GroupBotLocator.MODE_AUTO)
        else:
            raise ValueError(f"不支持的清理模式: {mode_name}")
        time.sleep(0.5)

    # 点击完成按钮
    def click_finish(self):
        """点击右上角/底部的完成按钮"""
        logger.info("⚙️ [Action-GroupBotPage] 点击【完成】以保存清理规则")
        self.click(GroupBotLocator.FINISH_BTN)
        time.sleep(1)

    # 在任务记录/通知中确认清理名单
    def confirm_clean_task(self):
        """在任务记录/通知中确认清理名单"""
        logger.info("⚙️ [Action-GroupBotPage] 点击【确认名单】")
        self.click(GroupBotLocator.CONFIRM_CLEAN_LIST)
        time.sleep(0.5)
        self.click_confirm()
        time.sleep(1)

    # 放弃本次清理
    def cancel_clean_task(self):
        """放弃本次清理"""
        logger.info("⚙️ [Action-GroupBotPage] 点击【放弃本次清理】")
        self.click(GroupBotLocator.CANCEL_CLEAN_TASK)
        time.sleep(0.5)
        self.click_confirm()
        time.sleep(1)

    # ==========================
    # 入群验证页面细化操作
    # ==========================

    # 一键配置入群验证规则
    def configure_join_verify(self, action_type: str = "仅移出群组", verify_time: str = "5min"):
        """一键配置入群验证规则"""
        logger.info(f"⚙️ [Action-GroupBotPage] 配置入群验证: 方式=点验, 时间={verify_time}, 处理={action_type}")
        
        # 1. 选择验证方式为点验
        self.click(GroupBotLocator.VERIFY_MODE_CLICK)
        time.sleep(0.5)
        
        # 2. 设置验证时间
        self.click(GroupBotLocator.VERIFY_TIME_ROW)
        time.sleep(1)
        time_option = (AppiumBy.ANDROID_UIAUTOMATOR, f'newUiSelector().text("{verify_time}")')
        self.click(time_option)
        time.sleep(0.5)
        
        # 3. 设置处理方式
        if action_type == "仅移出群组":
            self.click(GroupBotLocator.VERIFY_ACTION_KICK)
        elif action_type == "移除并拉黑":
            self.click(GroupBotLocator.VERIFY_ACTION_BLOCK)
        time.sleep(0.5)
        
        # 4. 默认验证所有新成员
        self.click(GroupBotLocator.VERIFY_SCOPE_ALL)
        time.sleep(0.5)

    # 新成员待验证态点击去验证按钮
    def go_verify(self):
        """新成员待验证态点击去验证按钮"""
        logger.info("⚙️ [Action-GroupBotPage] 点击【去验证】")
        self.click(GroupBotLocator.GO_VERIFY_BTN)
        time.sleep(2)

    # ==========================
    # 5. 进群欢迎语页面操作
    # ==========================

    # 进入【进群欢迎语】设置页
    def enter_welcome(self):
        """进入【进群欢迎语】设置页"""
        logger.info("⏳ [Action-GroupBotPage] 进入【进群欢迎语】设置页")
        self.click(GroupBotLocator.WELCOME_ENTRY)
        time.sleep(1)

    # 配置并完成进群欢迎语
    def configure_welcome(self, content: str):
        """配置并完成进群欢迎语"""
        logger.info(f"⚙️ [Action-GroupBotPage] 配置进群欢迎语: {content}")
        
        # 尝试点击“添加欢迎语”或“修改欢迎语”
        try:
            add_btn = self.find_elements(GroupBotLocator.WELCOME_ADD_BTN, timeout=2)
            if add_btn:
                logger.info("⚙️ [Action-GroupBotPage] 点击【添加欢迎语】")
                self.click(add_btn[0])
                time.sleep(1)
            else:
                edit_btn = self.find_elements(GroupBotLocator.WELCOME_EDIT_BTN, timeout=2)
                if edit_btn:
                    logger.info("⚙️ [Action-GroupBotPage] 点击【修改欢迎语】")
                    self.click(edit_btn[0])
                    time.sleep(1)
        except Exception as e:
            logger.warning(f"⚠️ [Action-GroupBotPage] 查找添加/修改按钮异常: {e}")

        # 清空并输入欢迎语内容
        input_field = self.find_element(GroupBotLocator.WELCOME_INPUT)
        input_field.clear()
        if content:
            input_field.send_keys(content)
            time.sleep(0.5)

        # 点击完成保存
        self.click(GroupBotLocator.WELCOME_FINISH_BTN)
        time.sleep(1.5)

    # ==========================
    # 6. 定时消息页面操作
    # ==========================

    # 进入【定时消息】页
    def enter_timed_msg(self):
        """进入【定时消息】页"""
        logger.info("⏳ [Action-GroupBotPage] 进入【定时消息】页")
        self.click(GroupBotLocator.TIMED_MSG_ENTRY)
        time.sleep(1)

    # 添加定时消息
    def add_timed_msg(self, content: str):
        """添加定时消息"""
        logger.info(f"⚙️ [Action-GroupBotPage] 准备添加定时消息: {content}")
        self.click(GroupBotLocator.ADD_TIMED_MSG_BTN)
        time.sleep(1)

        # 输入文本
        input_field = self.find_element(GroupBotLocator.TIMED_MSG_INPUT)
        input_field.clear()
        input_field.send_keys(content)
        time.sleep(0.5)

        # 设置时间
        self.click(GroupBotLocator.TIMED_MSG_TIME_ROW)
        time.sleep(1)
        self.click_confirm()  # 时间确认弹窗
        time.sleep(0.5)

        # 确认添加
        self.click(GroupBotLocator.TIMED_MSG_CONFIRM_BTN)
        time.sleep(0.5)
        self.click_confirm()  # 二次确认
        time.sleep(1)

    # 根据内容模糊匹配删除定时消息任务
    def delete_timed_msg(self, content_pattern: str):
        """根据内容模糊匹配删除定时消息任务"""
        logger.info(f"⚙️ [Action-GroupBotPage] 准备删除定时消息，内容匹配: {content_pattern}")
        # 点击指定条目的修改按钮进入编辑页
        # 定位特定内容的条目下的“修改”按钮
        modify_btn_loc = (AppiumBy.ANDROID_UIAUTOMATOR, 
                          f'newUiSelector().textContains("{content_pattern}").fromParent(newUiSelector().text("修改"))')
        try:
            self.click(modify_btn_loc)
            time.sleep(1)
            # 点击删除
            self.click(GroupBotLocator.TIMED_MSG_DELETE_BTN)
            time.sleep(0.5)
            self.click_confirm()
            time.sleep(1)
            logger.info("⚙️ [Action-GroupBotPage] 成功删除定时消息")
        except Exception as e:
            logger.warning(f"⚠️ [Action-GroupBotPage] 删除定时消息异常: {e}")
