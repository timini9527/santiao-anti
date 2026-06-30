import pytest
import allure
import time
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.groups.bot.group_bot_page import GroupBotPage
from pages.chat.chat_page import ChatPage
from pages.chat.chat_list_page import ChatListPage
from strategy.chat.chat_strategy import GROUP_STRATEGY
from utils.file_reader.data_loader import load_yaml_data

# 加载外部测试数据
keyword_yaml_data = load_yaml_data('groups/bot/keyword_rules.yaml')
keyword_rules = keyword_yaml_data.get("test_data", {}).get("keyword_validation", [])
keyword_params = [
    (d["data"]["keyword"], d["expected"]["action"], d["expected"].get("expected_text", ""), d["title"]) 
    for d in keyword_rules
]
keyword_ids = [d["title"] for d in keyword_rules]

# 元数据
origin_list = ['您发送的信息已被撤回 🌟请勿发送与本群无关的内容', '您发送的消息包含敏感内容已被撤回，请注意：多次违规将被禁言或移除聊天⚠️', '刚才的消息不太合适哦～我们一起维护良好的聊天环境吧！', '请勿刷屏，保持良好聊天环境', '友善提醒：刚才的消息不太合适呢～已帮你撤回啦，我们一起保持群内整洁吧！❤️', '再次提醒：请注意发言内容，本次已撤回处理', '违规警告：您发送的内容严重违反群规，已撤回处理，请注意发言内容~']


@allure.epic("IM核心功能测试")
@allure.feature("群助手-禁止发送关键词")
class TestGroupBotKeyword:
    """群助手禁止发送关键词功能测试"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self, driver_sender):
        """初始化发送方的页面对象"""
        self.mainS = MainPage(driver_sender)
        self.homeS = HomePage(driver_sender)
        self.chatListS = ChatListPage(driver_sender)
        self.chatS = ChatPage(driver_sender)
        self.settingS = GroupSettingPage(driver_sender)
        self.botS = GroupBotPage(driver_sender)

        yield
        
        self.mainS.go_to_main_page()

    @pytest.fixture
    def cleanup_keyword_settings(self):
        """用例后置清理：确保禁用禁发关键词检测，恢复群聊环境"""
        yield

        logger.info("🧹 [Cleanup] 开始清理群助手禁发关键词设置...")
        try:
            self.mainS.go_to_main_page()
            self.chatListS.enter_chat(GROUP_STRATEGY.name)
            self.chatS.wait_for_chat_page_load()
            self.chatS.click_more_button()
            self.settingS.wait_for_setting_page_load()
            self.settingS.click_friend_header()
            self.botS.enter_keyword_block()
            self.botS.toggle_keyword_detection_switch(enable=False)
            self.botS.click_save()
            logger.info("🧹 [Cleanup] 成功关闭群助手禁发关键词设置")
        except Exception as e:
            logger.warning(f"⚠️ [Cleanup] 清理禁发关键词设置时发生异常: {e}")

    def _enter_keyword_config_page(self):
        """辅助方法：进入关键词配置页并开启功能开关"""
        self.chatListS.enter_chat(GROUP_STRATEGY.name)
        self.chatS.wait_for_chat_page_load()
        self.chatS.click_more_button()
        self.settingS.wait_for_setting_page_load()
        self.settingS.click_friend_header()
        self.botS.wait_for_group_bot_page_load()
        self.botS.enter_keyword_block()
        self.botS.toggle_keyword_detection_switch(enable=True)
        self.botS.click_save()
    

    def _exit_keyword_config_page(self):
        """辅助方法：退出并返回聊天主页"""
        self.botS.click_back()
        self.botS.click_back()



    # TODO：特殊字符未正确拦截，待修复
    @allure.story("禁发关键词-添加关键词验证，合规与拦截规则")
    @allure.title("校验关键词输入限制与有效性: {description}-状态：已完成")
    @pytest.mark.parametrize("keyword, expected_action, expected_text, description", keyword_params, ids=keyword_ids)
    def test_keyword_add_with_various_char_types(self, keyword, expected_action, expected_text, description):
        """验证关键词输入规则：最多10字，且不支持邮箱和特殊符号的组合测试"""

        with allure.step("1. 进入关键词配置列表"):
            self._enter_keyword_config_page()
            self.botS.click_keyword_row()
        
        try:
            with allure.step(f"2. 填入测试词: {keyword}"):
                if expected_action == "success":
                    # 正向合规预期，直接设置并保存
                    self.botS.set_keywords([keyword])
                    self.botS.save_keywords_config()
                else:
                    # 逆向拦截预期，逐字输入以精确捕捉拦截行为
                    self.botS.input_keyword(keyword)
                    actual_text = self.botS.get_keyword_input_text()

            with allure.step(f"3. 校验行为: {expected_action}"):
                if expected_action == "success":
                    summary = self.botS.get_keyword_summary()
                    check.is_true(keyword in summary, f"保存合规关键词 {keyword} 失败，实际摘要为: {summary}")
                elif expected_action == "truncate":
                    check.equal(actual_text, expected_text, f"超长字符预期截断为: {expected_text}，实际为: {actual_text}")
                    self.botS.save_keywords_config()
                elif expected_action == "toast_or_clear":
                    # 拦截机制 1：输入框自动过滤
                    if actual_text == expected_text or actual_text == "" or actual_text == "testabccom" or actual_text == "abc":
                        logger.info(f"✅ {description} 已被输入框实时过滤拦截 (当前文本: '{actual_text}')")
                    else:
                        # 拦截机制 2：保存时弹窗阻断
                        self.botS.save_keywords_config()
                        toast = self.botS.get_toast()
                        check.is_true(
                            toast and ("格式" in toast or "符号" in toast or "不支持" in toast or "失败" in toast or "非法" in toast), 
                            f"未正确拦截非法字符，也没出现有效的拦截Toast，实际获取Toast为: {toast}"
                        )
        finally:
            with allure.step("4. 环境清理"):
                if expected_action in ["success", "truncate"]:
                    self.botS.click_keyword_row()
                self.botS.clear_all_keywords()
                self._exit_keyword_config_page()


    @allure.story("禁发关键词-添加关键词验证")
    @allure.title("校验最多添加 50 个关键词上限-状态：已完成")
    @pytest.mark.parametrize("length", [0, 1, 50, 51], ids=["添加 0 个关键词", "添加第1个关键词", "添加第50个关键词", "添加第51个关键词"])
    def test_keyword_max_limit(self, length):
        """验证关键词最多只能添加 50 个的边界及上限提示"""

        with allure.step("1. 配置群助手-禁发关键词"):
            self._enter_keyword_config_page()
            self.botS.click_keyword_row()
        
        try:
            with allure.step("2. 添加 0 - 50 个关键词"):
                keywords_list = [f"K{i}" for i in range(0, length)]
                count = self.botS.set_keywords(keywords=keywords_list)
                
                if length == 0:
                    check.equal(count, 0, f"添加关键词数量与预期不符，预期: {0}, 实际: {count}")
                    toast = self.botS.get_toast()
                    check.is_true("有未填写项，无法新增" in toast, f"未提示有未填写项，无法新增, Toast为: {toast}")

                if length != 51 and length != 0:
                    self.botS.save_keywords_config()
                    check.equal(count, length, f"添加关键词数量与预期不符，预期: {length}, 实际: {count}")
                    summary = self.botS.get_keyword_summary()
                    check.is_not_in("未设置" , summary, f"关键词数量与预期不符，预期: 未设置，实际: {summary}")

            
            with allure.step("3. 验证添加第51个关键词"):
                if length == 51:
                    self.botS.click_keyword_add_btn()
                    toast = self.botS.get_toast()
                    check.is_true("当前最多可设置50个关键词" in toast, f"未提示最多，Toast为: {toast}")
                    self.botS.click_back()
                    summary = self.botS.get_keyword_summary()
                    check.is_true("未设置" in summary, f"关键词数量与预期不符，预期: 50个，实际: {summary}")
                    # self.botS.click_keyword_add_btn()
        finally:
            if length in [1, 50]:
                self.botS.enter_keyword_block()
                self.botS.click_keyword_row()
                self.botS.clear_all_keywords()
                self._exit_keyword_config_page()
            elif length == 51:
                # self.botS.clear_keyword_input()
                # self.botS.clear_all_keywords()
                self._exit_keyword_config_page()
            else:
                self._exit_keyword_config_page()


    @allure.story("禁发关键词-删除/清空关键词")
    @allure.title("校验删除关键词成功-状态：已完成")
    @pytest.mark.parametrize("del_index", (1, 0), ids=["删除第1个关键词", "清空所有关键词"])
    def test_keyword_delete(self, del_index):
        """验证删除关键词功能"""
        with allure.step("1. 配置群助手-禁发关键词"):
            self._enter_keyword_config_page()
            self.botS.click_keyword_row()
        
        try:
            with allure.step("2. 添加 5 个关键词并保存"):
                keywords_list = [f"K{i}" for i in range(0, 5)]
                self.botS.set_keywords(keywords=keywords_list)
                self.botS.save_keywords_config()
                
                summary = self.botS.get_keyword_summary()
                check.is_not_in("未设置", summary, f"关键词数量与预期不符，实际为: {summary}")

            with allure.step(f"3. 再次进入配置页，执行 {'删除第1个' if del_index == 1 else '清空全部'} 关键词"):
                self.botS.click_keyword_row()
                keyword_row_count = self.botS.get_keyword_row_count()
                check.equal(keyword_row_count, 5, f"列表初始数量不为5，实际: {keyword_row_count}")
                
                delete_count = 1 if del_index == 1 else None
                self.botS.clear_all_keywords(count=delete_count)
                
            with allure.step("4. 校验删除结果"):
                if del_index == 1:
                    self.botS.click_keyword_row()
                    new_count = self.botS.get_keyword_row_count()
                    check.equal(new_count, 4, f"删除1个后，列表剩余数量应为4，实际: {new_count}")
                    self.botS.save_keywords_config()
                else:
                    summary = self.botS.get_keyword_summary()
                    check.is_true("未设置" in summary, f"清空全部后，配置摘要应为未设置，实际: {summary}")
        finally:
            with allure.step("5. 环境清理"):
                self.botS.enter_keyword_block()
                self.botS.click_keyword_row()
                self.botS.clear_all_keywords()
                self._exit_keyword_config_page()
    
    
    @allure.story("禁发关键词-输入规则限制")
    @allure.title("校验删除关键词二次确认流程-状态：已完成: {confirm_action}")
    @pytest.mark.parametrize("confirm_action", ["confirm", "cancel"], ids=["确认删除", "取消删除"])
    def test_keyword_delete_flow(self, confirm_action):
        """验证删除关键词时的二次确认弹窗的取消和确定逻辑"""
        with allure.step("1. 进入关键词配置页"):
            self._enter_keyword_config_page()
            self.botS.click_keyword_row()
            
        try:
            with allure.step("2. 输入内容触发删除按钮"):
                keywords_list = ['取消删除', '确认删除']
                self.botS.set_keywords(keywords=keywords_list)
                self.botS.save_keywords_config()
                self.botS.click_keyword_row()
                check.is_true(len(self.botS.get_keyword_delete_icon_list()) > 0, "输入内容后未显示删除按钮")
            
            with allure.step("3. 点击删除，校验弹窗"):
                delete_icons = self.botS.get_keyword_delete_icon_list()
                if delete_icons:
                    delete_icons[0].click()
                check.is_true(self.botS.get_confirm_dialog(), "未弹出二次确认弹窗")
            
            with allure.step(f"4. 执行操作: {confirm_action}并校验"):
                if confirm_action == "cancel":
                    self.botS.click_keyword_delete_cancel_btn()
                    check.equal(self.botS.get_keyword_row_count(), 2, "取消删除后关键词数量应该不变")
                    rows = self.botS.get_keyword_row_element()
                    if rows:
                        check.equal(rows[0].get_attribute("text"), "确认删除", "取消删除后关键词内容改变")
                else:
                    self.botS.click_keyword_delete_confirm_btn()
                    check.equal(self.botS.get_keyword_row_count(), 1, "确认删除后关键词数量应该减少1个")
                    rows = self.botS.get_keyword_row_element()
                    if rows:
                        check.equal(rows[0].get_attribute("text"), "取消删除", "被删除后的剩余关键词不正确")
        finally:
            with allure.step("5. 环境清理"):
                self.botS.clear_all_keywords()
                self._exit_keyword_config_page()

    
    @allure.story("禁发关键词-警告语设置-添加")
    @allure.title("自定义警告语 - 配置校验与上限测试-状态：已完成")
    @pytest.mark.parametrize("warning_count, warning_msg", [
        (0, None), 
        (1, ["第一条警告语"]),
        (2, ["警告语敏感词：习近平"]),
        (3, [f"自定义警告语{i+1}" for i in range(10)]),
        (4, [f"超出上限的警告语{i+1}" for i in range(11)])],
        ids=["添加0条警告语", "添加1条警告语", "添加敏感词警告语", "添加警告语到上限", "添加超过10条警告语"])
    def test_group_bot_keyword_warning_message_setting(self, warning_count, warning_msg):
        """验证配置自定义警告语的规则与数量上限，包括空输入拦截和批量添加的边界值校验"""
        
        with allure.step("1. 发送方进入群助手，进入警告语设置面板"):
            self._enter_keyword_config_page()
            before_warning_msg_text = self.botS.get_warning_msg_text()
            self.botS.click_warning_msg_setting()
            self.botS.wait_warning_msg_panel()
        
        with allure.step("2. 获取元素默认值警告语"):
            default_msg = self.botS.get_all_warning_msg_texts()
            before_warning_msg_count = len(default_msg)
        
        with allure.step(f"3. 设置自定义警告语：{warning_msg}"):
            if warning_count not in [0, 2]:
                count = len(warning_msg) - before_warning_msg_count
                warning_msg = warning_msg[:count]
            
            self.botS.set_custom_warning_msg(msgs=warning_msg)
            new_warning_msg = self.botS.get_warning_msg_text()

            if warning_msg is None and warning_count == 0:
                warning_toast = self.botS.get_toast()
                check.is_true("请输入警告语" in warning_toast, f"未触发空输入拦截 Toast，实际为: {warning_toast}")
                check.equal(new_warning_msg, before_warning_msg_text, "设置自定义警告语为空后，文本不正确")
                self.botS.click_custom_warning_msg_cancel_btn()
            elif warning_count == 2:
                warning_toast = self.botS.get_toast()
                check.is_true("内容包含敏感词，请修改后提交" in warning_toast, f"未触发敏感词拦截 Toast，实际为: {warning_toast}")
                check.equal(new_warning_msg, before_warning_msg_text, "设置自定义警告语为敏感词后，文本不正确")
                self.botS.click_custom_warning_msg_cancel_btn()
            elif warning_count == 4:
                warning_toast = self.botS.get_toast()
                check.is_true("当前最多可设置10条警告语" in warning_toast, f"未触发超限拦截 Toast，实际为: {warning_toast}")
                check.equal(new_warning_msg, before_warning_msg_text, "设置自定义警告语超限后，文本不应改变")
                self.botS.click_custom_warning_msg_cancel_btn()
            else:
                check.not_equal(new_warning_msg, before_warning_msg_text, "设置自定义警告语后文本不正确")
        
        with allure.step("4. 设置自定义警告语后数量"):  
            if not self.botS.wait_warning_msg_panel():
                self.botS.click_warning_msg_setting()
                self.botS.wait_warning_msg_panel()
            
            after_warning_msg_count = self.botS.get_warning_msg_count()
            if warning_count in [0, 2, 4]:
                expected_added = 0 
            else:
                expected_added = len(warning_msg) if warning_msg else 0
            check.equal(after_warning_msg_count, before_warning_msg_count + expected_added, "设置自定义警告语后数量不正确")
        

    @allure.story("禁发关键词-警告语设置 - 删除")
    @allure.title("删除自定义警告语-状态：已完成")
    @pytest.mark.parametrize("action, target_index, is_confirm", [
        ("delete_custom", 1, True),    
        ("delete_custom", 1, False),  
        ("delete_last_one", 0, True)   
        ], ids=["删除单条_确认", "删除单条_取消", "尝试删除最后一条警告语拦截"])
    def test_group_bot_keyword_delete_warning_msg(self, action, target_index, is_confirm):
        """验证删除自定义警告语的功能"""

        with allure.step("1. 发送方进入群助手，进入警告语设置面板"):
            self._enter_keyword_config_page()
            before_warning_msg_text = self.botS.get_warning_msg_text()
            self.botS.click_warning_msg_setting()
            self.botS.wait_warning_msg_panel()
            
        with allure.step("2. 前置准备测试数据"):
            current_count = self.botS.get_warning_msg_count()
            if action == "delete_custom":
                if current_count < 2:
                    self.botS.set_custom_warning_msg(origin_list)
                    if not self.botS.wait_warning_msg_panel(timeout=2):
                        self.botS.click_warning_msg_setting()
                        self.botS.wait_warning_msg_panel()
                    current_count = self.botS.get_warning_msg_count()
            elif action == "delete_last_one":
                pass 
        
        with allure.step("3. 向下滑动"):
            if current_count > 5:
                self.botS.scroll_warning_msg_list_down()

        with allure.step(f"4. 触发删除动作: target_index={target_index}"):
            warning_texts = self.botS.get_current_page_warning_msg_texts()
            target_text = warning_texts[target_index] if len(warning_texts) > target_index else None
            self.botS.delete_warning_msg(index=target_index)

        with allure.step(f"5. 执行操作: {is_confirm} 并校验结果"):
            if action == "delete_last_one":
                self.botS.click_custom_warning_msg_confirm_btn()
                warning_toast = self.botS.get_toast()
                check.is_true("至少保留一条警告语" in warning_toast, f"未触发最后一条警告语拦截Toast，实际为: {warning_toast}")
            else:
                if not is_confirm:
                    self.botS.click_custom_warning_msg_cancel_btn()
                    self.botS.click_warning_msg_setting()
                    self.botS.wait_warning_msg_panel()
                    current_texts = self.botS.get_all_warning_msg_texts()
                    check.equal(len(current_texts), current_count, "取消删除后，警告语数量不应改变")
                    check.equal(current_texts, warning_texts, "取消删除后，警告语内容不应改变")
                else:
                    self.botS.click_custom_warning_msg_confirm_btn()
                    self.botS.click_warning_msg_setting()
                    self.botS.wait_warning_msg_panel()
                    current_texts = self.botS.get_all_warning_msg_texts()
                    check.equal(len(current_texts), current_count - 1, "确认删除后，警告语数量没有减少")
                    if target_text:
                        check.is_false(target_text in current_texts, f"确认删除后，被删警告语 {target_text} 仍然存在于列表中")
        
        with allure.step("6. 测试环境后置：恢复初始警告语"):
            if action == "delete_last_one":
                logger.info("⚙️ 正在恢复 delete_last_one 测试删除掉的警告语数据...")
                self.botS.set_custom_warning_msg(origin_list)
















