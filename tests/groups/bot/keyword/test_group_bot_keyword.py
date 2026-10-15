import time
import pytest
import allure
import pytest_check as check
from core.logger_utils import logger, LogIcon
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.groups.bot.group_bot_page import GroupBotPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from strategy.chat.chat_strategy import GROUP_STRATEGY
from utils.file_reader.data_loader import load_yaml_data


keyword_yaml_data = load_yaml_data('groups/bot/keyword_rules.yaml')
test_data = keyword_yaml_data.get("test_data", {})

# 1. 单个关键词合规录入（中文、字母、数字、混合，刚好10字边界）
valid_single_params = [
    pytest.param(d["data"]["keyword"], d["expected"]["expected_word"], d["title"], id=d["title"])
    for d in test_data.get("valid_single_keywords", [])
]

# 2. 空格批量添加分词（核心新 UI 特性）
batch_space_params = [
    pytest.param(d["data"]["input_text"], d["expected"]["expected_words"], d["title"], id=d["title"])
    for d in test_data.get("batch_by_space_keywords", [])
]

# 3. 超过10字截断
truncate_params = [
    pytest.param(d["data"]["keyword"], d["expected"]["truncated_text"], d["title"], id=d["title"])
    for d in test_data.get("length_truncate_keywords", [])
]

# 4. 非法字符拦截
invalid_chars_params = [
    pytest.param(d["data"]["keyword"], d["title"], id=d["title"])
    for d in test_data.get("invalid_characters_keywords", [])
]


origin_list = [
    '您发送的信息已被撤回 🌟请勿发送与本群无关的内容', 
    '您发送的消息包含敏感内容已被撤回，请注意：多次违规将被禁言或移除聊天⚠️',
    '刚才的消息不太合适哦～我们一起维护良好的聊天环境吧！', 
    '请勿刷屏，保持良好聊天环境', 
    '友善提醒：刚才的消息不太合适呢～已帮你撤回啦，我们一起保持群内整洁吧！❤️', 
    '再次提醒：请注意发言内容，本次已撤回处理', 
    '违规警告：您发送的内容严重违反群规，已撤回处理，请注意发言内容~'
]


@allure.epic("IM核心功能测试")
@allure.feature("群助手-禁止发送关键词")
class TestGroupBotKeyword:
    """群助手禁止发送关键词功能测试"""

    mainS: MainPage
    homeS: HomePage
    chatListS: ChatListPage
    chatS: ChatPage
    settingS: GroupSettingPage
    botS: GroupBotPage

    @pytest.fixture(autouse=True)
    def setup_method(self, request, driver_sender):
        """初始化发送方的页面对象"""
        self.mainS = MainPage(driver_sender)
        self.homeS = HomePage(driver_sender)
        self.chatListS = ChatListPage(driver_sender)
        self.chatS = ChatPage(driver_sender)
        self.settingS = GroupSettingPage(driver_sender)
        self.botS = GroupBotPage(driver_sender)

        yield
        
        if "cleanup_keyword_settings" in request.fixturenames or "cleanup_warning_settings" in request.fixturenames:
            return

        self.mainS.go_to_main_page()

    @pytest.fixture
    def cleanup_warning_settings(self, request):
        """警告语测试后置清理：保持在配置页连续执行，全部参数跑完后恢复默认警告语并返回主页"""
        yield

        node_name = request.node.name
        is_last = "添加至10条上限" in node_name or "尝试删除最后一条警告语拦截" in node_name
        if not is_last:
            return

        logger.info(f"{LogIcon.SETUP} 警告语测试完毕，恢复初始默认警告语并安全返回主页...")
        try:
            current_count = self.botS.get_warning_msg_count()
            if current_count > 7:
                self.botS.clear_extra_warning_msgs(nums=current_count, target_remain=7)
            elif current_count < 7:
                self.botS.set_custom_warning_msg(origin_list[:7 - current_count])

            self.botS.toggle_switch(enable=False)
            self.botS.click_save()
            self.mainS.go_to_main_page()
            logger.info(f"{LogIcon.SETUP} 成功恢复默认警告语并返回主页")
        except Exception as e:
            logger.warning(f"{LogIcon.WARN} 警告语后置恢复异常: {e}")
            self.mainS.go_to_main_page()

    @pytest.fixture
    def cleanup_keyword_settings(self, request):
        """用例后置清理：在全部参数执行完后才退回主页并关闭群助手禁发关键词设置"""
        yield

        is_last_case = False
        node_name = request.node.name
        last_candidates = [
            "取消删除",
            "清空所有关键词",
            "添加第51个关键词",
            invalid_chars_params[-1].id if invalid_chars_params else None,
            batch_space_params[-1].id if batch_space_params else None,
            truncate_params[-1].id if truncate_params else None,
            valid_single_params[-1].id if valid_single_params else None,
        ]
        if any(c and (node_name.endswith(f"[{c}]") or c in node_name) for c in last_candidates):
            is_last_case = True

        if not is_last_case:
            return

        logger.info(f"{LogIcon.SETUP} 关键词新增规则验证完毕，执行环境清理并安全返回主页...")
        try:
            self.botS.cancel_keyword_dialog_if_displayed()
            self.botS.clear_all_keywords()
            self.botS.click_back()
            self.botS.toggle_switch(enable=False)
            self.botS.click_save()
            self.mainS.go_to_main_page()
            logger.info(f"{LogIcon.SETUP} 成功关闭群助手禁发关键词设置并返回主页")
        except Exception as e:
            logger.warning(f"{LogIcon.WARN} 清理禁发关键词设置时发生异常: {e}")
            self.mainS.go_to_main_page()


    def _enter_keyword_config_page(self) -> None:
        """从主页导航进入关键词配置页并开启功能开关"""
        self.mainS.go_to_main_page()
        self.chatListS.enter_chat(GROUP_STRATEGY.name)
        self.chatS.wait_for_chat_page_load()
        self.chatS.click_more_button()
        self.settingS.wait_for_setting_page_load()
        self.settingS.click_friend_header()
        self.botS.wait_for_group_bot_page_load()
        self.botS.enter_keyword_block()
        self.botS.toggle_switch(enable=True)
        self.botS.click_save()

    def _ensure_in_keyword_config_page(self) -> None:
        """智能确保当前处于禁发关键词功能配置页"""
        if not self.botS.is_in_keyword_config_page(timeout=0.5):
            self._enter_keyword_config_page()

    def _ensure_in_keyword_list_page(self) -> None:
        """智能确保当前处于关键词配置列表页（零多余导航，彻底消灭每次回主页）"""
        if not self.botS.is_in_keyword_list_page(timeout=0.5):
            self._ensure_in_keyword_config_page()
            self.botS.click_keyword_row()



    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("禁发关键词-添加关键词验证-单词合规录入")
    @allure.title("校验单个关键词合规录入与10字上限: {title}-状态：已完成")
    @pytest.mark.usefixtures("cleanup_keyword_settings")
    @pytest.mark.parametrize("keyword, expected_word, title", valid_single_params)
    def test_keyword_add_valid_single(self, keyword: str, expected_word: str, title: str):
        """验证新UI规则：单个关键词最多10个字，仅支持中文、字母和数字"""
        with allure.step("1. 进入关键词配置列表页"):
            self._ensure_in_keyword_list_page()

        with allure.step(f"2. 点击新增弹窗录入关键词: {keyword}"):
            keywords_list = self.botS.get_keyword_list()
            if keyword not in keywords_list:
                self.botS.click_keyword_add_btn()
                self.botS.input_keywords(keyword)
                self.botS.click_confirm_btn()
            else:
                logger.info(f"{LogIcon.WARN} 关键词 {keyword} 已存在，跳过新增")

        with allure.step(f"3. 校验关键词已成功添加至列表: {expected_word}"):
            keyword_list = self.botS.get_keyword_list()
            check.is_true(expected_word in keyword_list, f"关键词列表未包含预期词: {expected_word}，实际列表: {keyword_list}")


    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("禁发关键词-添加关键词验证-空格批量分词")
    @allure.title("校验空格分隔批量添加关键词: {title}-状态：已完成")
    @pytest.mark.usefixtures("cleanup_keyword_settings")
    @pytest.mark.parametrize("input_text, expected_words, title", batch_space_params)
    def test_keyword_batch_add_by_space(self, input_text: str, expected_words: list[str], title: str):
        """验证新UI规则：批量添加请用空格分隔，如：红包 广告 刷单"""
        with allure.step("1. 进入关键词配置列表页"):
            self._ensure_in_keyword_list_page()

        with allure.step(f"2. 弹窗输入空格分隔文本: '{input_text}'"):
            self.botS.clear_all_keywords()
            self.botS.click_keyword_add_btn()
            self.botS.input_keywords(input_text)
            self.botS.click_confirm_btn()

        with allure.step(f"3. 校验列表已同时批量新增所有分词: {expected_words}"):
            keyword_list = self.botS.get_keyword_list()
            for word in expected_words:
                check.is_true(word in keyword_list, f"批量添加分词失败，列表缺失词: {word}，实际列表: {keyword_list}")


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story("禁发关键词-输入规则限制-长度限制")
    @allure.title("校验超过10字超长拦截与截断录入规则: {title}-状态：已完成")
    @pytest.mark.usefixtures("cleanup_keyword_settings")
    @pytest.mark.parametrize("keyword, truncated_text, title", truncate_params)
    def test_keyword_add_length_truncate(self, keyword: str, truncated_text: str, title: str):
        """验证新UI规则：单个关键词最多10个字。超长字符不会自动截断入库，系统弹出Toast拦截；需手动截断为前10字方可成功提交入库"""
        with allure.step("1. 进入关键词配置列表页"):
            self._ensure_in_keyword_list_page()

        with allure.step(f"2. 弹窗输入超长字符并校验拦截: {keyword}"):
            self.botS.click_keyword_add_btn()
            self.botS.input_keywords(keyword)
            self.botS.click_confirm_btn()
            toast_exist = self.botS.verify_toast_exist("单个关键词最多10个字")
            check.is_true(toast_exist, "超长关键词提交后未捕获到'单个关键词最多10个字'的Toast拦截提示")

        with allure.step(f"3. 手动截断超出部分（保留前10字），再次提交并校验入库"):
            valid_keyword = keyword[:10]
            self.botS.input_keywords(valid_keyword)
            self.botS.click_confirm_btn()

            keyword_list = self.botS.get_keyword_list()
            check.is_in(
                valid_keyword, 
                keyword_list, 
                f"截断前10字后的关键词未成功入库，预期包含: '{valid_keyword}'，实际列表: {keyword_list}"
            )
            self.botS.clear_all_keywords()


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story("禁发关键词-输入规则限制-非法字符拦截")
    @allure.title("校验非法字符拦截规则: {title}-状态：已完成")
    @pytest.mark.usefixtures("cleanup_keyword_settings")
    @pytest.mark.parametrize("keyword, title", invalid_chars_params)
    def test_keyword_add_invalid_characters(self, keyword: str, title: str):
        """验证新UI规则：仅支持中文、字母和数字，特殊符号/邮箱等无法输入或点击确定被拦截"""
        with allure.step("1. 进入关键词配置列表页"):
            self._ensure_in_keyword_list_page()

        with allure.step(f"2. 弹窗录入非法格式字符: {keyword}"):
            self.botS.click_keyword_add_btn()
            self.botS.input_keywords(keyword)
            actual_text = self.botS.get_keywords_text()

        with allure.step("3. 校验输入框实时过滤或 Toast 拦截"):
            if not actual_text or not any(c.isalnum() for c in actual_text):
                logger.info(f"{LogIcon.SUCCESS} 非法字符 '{keyword}' 已被输入框实时过滤拦截 (当前文本为空或纯过滤)")
                self.botS.click_cancel_btn()
            else:
                self.botS.click_confirm_btn()
                toast = self.botS.get_toast()
                check.is_true(
                    toast and any(w in toast for w in ["特殊符号", "表情", "格式", "字符"]), 
                    f"未正确拦截非法字符 '{keyword}'，Toast 提示为: {toast}"
                )
                self.botS.click_cancel_btn()


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story("禁发关键词-添加关键词验证")
    @allure.title("校验最多添加 50 个关键词上限-状态：已完成")
    @pytest.mark.parametrize(
        "length",
        [
            pytest.param(0, id="添加 0 个关键词"),
            pytest.param(1, id="添加第1个关键词"),
            pytest.param(50, id="添加第50个关键词"),
            pytest.param(51, id="添加第51个关键词"),
        ],
    )
    @pytest.mark.usefixtures("cleanup_keyword_settings")
    def test_keyword_max_limit(self, length: int):
        """验证关键词最多只能添加 50 个的边界及上限提示"""
        with allure.step("1. 进入关键词配置列表页"):
            self._ensure_in_keyword_list_page()
        
        with allure.step(f"2. 测试添加数量分支: length={length}"):
            self.botS.clear_all_keywords()
            if length == 0:
                self.botS.click_keyword_add_btn()
                self.botS.click_confirm_btn()
                toast = self.botS.get_toast()
                check.is_true(
                    toast and any(w in toast for w in ["输入", "填写", "不能为空"]),
                    f"未提示输入拦截，实际 Toast 为: {toast}"
                )
                self.botS.click_cancel_btn()
                check.equal(self.botS.get_keyword_row_count(timeout=0.5), 0, "空提交不应增加关键词行")

            elif length in [1, 50]:
                keywords_list = [f"K{i} " for i in range(length)]
                self.botS.add_keywords(keywords_list)
                self.botS.click_back()
                summary = self.botS.get_keyword_summary()
                check.is_not_in("未设置", summary, f"添加 {length} 个关键词后，摘要不应为未设置，实际为: {summary}")
                self.botS.click_keyword_row()

            elif length == 51:
                self.botS.add_keywords([f"K{i} " for i in range(50)])
                time.sleep(2)
                self.botS.click_keyword_add_btn()
                toast = self.botS.verify_toast_exist("当前最多可设置50个关键词")
                check.is_true(toast, f"未提示达到50个关键词上限，实际 Toast 为: {toast}")
                self.botS.cancel_keyword_dialog_if_displayed()
            self.botS.clear_all_keywords()


    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("禁发关键词-删除/清空关键词")
    @allure.title("校验删除关键词成功-状态：已完成: {title}")
    @pytest.mark.usefixtures("cleanup_keyword_settings")
    @pytest.mark.parametrize(
        "del_count, is_empty_expected, title",
        [
            pytest.param(1, False, "删除单条关键词后列表与摘要保持有效", id="删除单条关键词"),
            pytest.param(None, True, "清空所有关键词后列表归零且摘要重置", id="清空所有关键词"),
        ],
    )
    def test_keyword_delete(self, del_count: int | None, is_empty_expected: bool, title: str):
        """验证删除关键词功能：覆盖单条删除与全量清空，及其对上级摘要状态的同步更新"""
        with allure.step("1. 智能确保进入关键词配置列表页并初始化环境"):
            self._ensure_in_keyword_list_page()
            self.botS.clear_all_keywords()
        
        with allure.step("2. 批量添加 5 个关键词准备测试环境"):
            keywords_list = [f"K{i} " for i in range(5)]
            self.botS.add_keywords(keywords_list)
            check.equal(self.botS.get_keyword_row_count(timeout=0.5), 5, "列表初始数量应为 5")

        with allure.step(f"3. 执行删除操作: {title}"):
            self.botS.clear_all_keywords(count=del_count)
            
        with allure.step("4. 校验列表剩余行数并返回上级验证摘要同步更新"):
            expected_remaining = 4 if del_count == 1 else 0
            remaining_count = self.botS.get_keyword_row_count(timeout=0.5)
            check.equal(remaining_count, expected_remaining, f"删除后列表行数不匹配，预期: {expected_remaining}，实际: {remaining_count}")
            self.botS.click_back()
            summary = self.botS.get_keyword_summary()
            if is_empty_expected:
                check.is_true("未设置" in summary, f"全部清空后摘要应为未设置，实际为: {summary}")
            else:
                check.is_not_in("未设置", summary, f"尚有剩余关键词时摘要不应为未设置，实际为: {summary}")
                self.botS.click_keyword_row()
                self.botS.clear_all_keywords()


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story("禁发关键词-输入规则限制")
    @allure.title("校验删除关键词二次确认流程-状态：已完成: {confirm_action}")
    @pytest.mark.usefixtures("cleanup_keyword_settings")
    @pytest.mark.parametrize(
        "confirm_action",
        [
            pytest.param("confirm", id="确认删除"),
            pytest.param("cancel", id="取消删除"),
        ],
    )
    def test_keyword_delete_flow(self, confirm_action: str):
        """验证删除关键词时的二次确认弹窗的取消和确定逻辑，验证数量变化及指定词精确移除"""
        with allure.step("1. 智能确保进入关键词配置列表页并初始化纯净环境"):
            self._ensure_in_keyword_list_page()
            self.botS.clear_all_keywords()
            
        with allure.step("2. 添加 2 个关键词准备测试数据"):
            target_del_word = "待删词A"
            keep_word = "留存词B"
            self.botS.add_keywords([f"{target_del_word} ", f"{keep_word} "])
            delete_icon_count = self.botS.get_keyword_delete_icon_count()
            check.is_true(delete_icon_count >= 2, f"关键词列表中删除按钮不足 2 个，实际: {delete_icon_count}")
        
        with allure.step(f"3. 点击第 1 个删除按钮（{target_del_word}），校验二次确认弹窗弹出"):
            self.botS.click_delete_keyword_icon(index=0)
            check.is_true(self.botS.get_confirm_dialog(), "未弹出删除二次确认弹窗")
        
        with allure.step(f"4. 执行操作: {confirm_action} 并精确校验列表数量与词条内容"):
            if confirm_action == "cancel":
                self.botS.click_keyword_delete_cancel_btn()
                current_list = self.botS.get_keyword_list()
                check.equal(len(current_list), 2, "取消删除后关键词数量应该不变（仍为 2）")
                check.is_true(target_del_word in current_list and keep_word in current_list, "取消删除后原词条内容应完整保留")
            else:
                self.botS.click_keyword_delete_confirm_btn()
                current_list = self.botS.get_keyword_list()
                check.equal(len(current_list), 1, "确认删除后关键词数量应该减少 1 个（剩余 1）")
                check.is_false(target_del_word in current_list, f"确认删除后，目标词 {target_del_word} 不应再存在于列表中")
                check.is_true(keep_word in current_list, f"确认删除后，非目标词 {keep_word} 应正常留存")

        with allure.step("5. 清理本次测试数据"):
            self.botS.clear_all_keywords()

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story("禁发关键词-警告语设置-添加")
    @allure.title("自定义警告语 - 配置校验与上限测试-状态：已完成: {title}")
    @pytest.mark.usefixtures("cleanup_warning_settings")
    @pytest.mark.parametrize(
        "case_type, input_msgs, expected_toast, title",
        [
            pytest.param("empty", None, "请输入警告语", "空输入拦截", id="空输入拦截"),
            pytest.param("sensitive", ["习近平"], "内容包含敏感词，请修改后提交", "敏感词拦截", id="敏感词拦截"),
            pytest.param("overflow", [f"超限词{i}" for i in range(11)], "当前最多可设置10条警告语", "超限10条拦截", id="超限10条拦截"),
            pytest.param("single", ["新增单条警告语"], None, "添加单条自定义警告语", id="添加单条警告语"),
            pytest.param("max_limit", [f"顶格词{i}" for i in range(10)], None, "添加警告语达到10条上限", id="添加至10条上限"),
        ],
    )
    def test_group_bot_keyword_warning_message_setting(
        self, case_type: str, input_msgs: list[str] | None, expected_toast: str | None, title: str
    ):
        """验证配置自定义警告语的规则与数量上限：覆盖空输入拦截、敏感词拦截、超限拦截及正常添加"""
        with allure.step("1. 智能确保进入群助手禁发关键词配置页并打开警告语面板"):
            self._ensure_in_keyword_config_page()
            self.botS.open_warning_msg_panel()
            before_count = len(self.botS.get_all_warning_msg_texts())
            if before_count >= 10:
                self.botS.clear_extra_warning_msgs(nums=before_count, target_remain=7)
                before_count = self.botS.get_warning_msg_count()

        with allure.step(f"2. 执行业务操作: {title}"):
            if case_type == "empty":
                self.botS.click_custom_warning_msg_btn()
                self.botS.click_custom_warning_msg_confirm_btn()
                toast = self.botS.get_toast()
                check.is_true(expected_toast in toast, f"未触发空输入拦截，实际 Toast: {toast}")

            elif case_type == "sensitive":
                self.botS.set_custom_warning_msg(msgs=input_msgs)
                toast = self.botS.get_toast()
                check.is_true(expected_toast in toast, f"未触发敏感词拦截 [{expected_toast}]，实际 Toast: {toast}")

            elif case_type == "overflow":
                overflow_msgs = input_msgs[: 10 - before_count + 1]
                self.botS.set_custom_warning_msg(msgs=overflow_msgs)
                toast = self.botS.get_toast()
                check.is_true(expected_toast in toast, f"未触发超限拦截 [{expected_toast}]，实际 Toast: {toast}")

            elif case_type == "single":
                self.botS.set_custom_warning_msg(msgs=input_msgs)
                self.botS.open_warning_msg_panel(force_reopen=True)
                after_count = self.botS.get_warning_msg_count()
                check.equal(after_count, before_count + 1, "新增单条警告语后数量未增加 1")

            elif case_type == "max_limit":
                needed = 10 - before_count
                if needed > 0 and input_msgs:
                    self.botS.set_custom_warning_msg(msgs=input_msgs[:needed])
                self.botS.open_warning_msg_panel(force_reopen=True)
                check.equal(self.botS.get_warning_msg_count(), 10, "添加至上限后总数未达到 10 条")


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story("禁发关键词-警告语设置 - 删除")
    @allure.title("删除自定义警告语-状态：已完成: {id_title}")
    @pytest.mark.usefixtures("cleanup_warning_settings")
    @pytest.mark.parametrize(
        "action, target_index, is_confirm, id_title",
        [
            pytest.param("delete_custom", 1, True, "删除单条_确认", id="删除单条_确认"),
            pytest.param("delete_custom", 1, False, "删除单条_取消", id="删除单条_取消"),
            pytest.param("delete_last_one", 0, True, "尝试删除最后一条警告语拦截", id="尝试删除最后一条警告语拦截"),
        ],
    )
    def test_group_bot_keyword_delete_warning_msg(self, action: str, target_index: int, is_confirm: bool, id_title: str):
        """验证删除自定义警告语的功能：覆盖删除确认生效、删除取消回退以及删除最后一条的业务拦截校验"""
        with allure.step("1. 确保进入群助手禁发关键词配置页并打开警告语面板"):
            self._ensure_in_keyword_config_page()
            self.botS.open_warning_msg_panel()

        with allure.step("2. 前置准备测试数据"):
            self.botS.cancel_warning_msg_dialog_if_displayed()
            current_count = self.botS.get_warning_msg_count()
            if action == "delete_custom" and current_count < 2:
                self.botS.set_custom_warning_msg(origin_list)
                current_count = self.botS.confirm_and_reopen_warning_panel()
            elif action == "delete_last_one" and current_count > 1:
                self.botS.clear_extra_warning_msgs(target_remain=1, nums=current_count)
            
            before_count = self.botS.confirm_and_reopen_warning_panel()

        with allure.step(f"3. 触发删除动作: target_index={target_index}"):
            self.botS.delete_warning_msg(index=target_index)

        with allure.step(f"4. 执行操作: {'确认' if is_confirm else '取消'} 并校验结果"):
            if action == "delete_last_one":
                self.botS.click_custom_warning_msg_confirm_btn()
                warning_toast = self.botS.get_toast()
                check.is_true("至少保留一条警告语" in warning_toast, f"未触发最后一条警告语拦截Toast，实际为: {warning_toast}")
                
            elif not is_confirm:
                self.botS.click_custom_warning_msg_cancel_btn()
                self.botS.open_warning_msg_panel()
                after_count = self.botS.get_warning_msg_count()
                check.equal(after_count, before_count, "取消删除后，警告语数量不应改变")

            else:
                after_count = self.botS.confirm_and_reopen_warning_panel()
                check.equal(after_count, before_count - 1, "确认删除后，警告语数量未减少 1")
