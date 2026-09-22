import pytest
import allure
import time
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.groups.setting.manager.group_manager_page import GroupManagerPage
from pages.groups.bot.group_bot_page import GroupBotPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_panel_page import ChatPanelPage
from pages.chat_options.voice.chat_voice_page import ChatVoicePage
from pages.chat_options.emojis.chat_emoji_page import ChatEmojiPage
from pages.chat_options.file.chat_file_page import ChatFilePage
from pages.mine.collection.chat_collection_page import ChatCollectionPage
from pages.chat.core.chat_long_press_page import ChatLongPressPage
from strategy.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY




@allure.epic('IM核心功能测试')
@allure.feature('群聊模块-群管理-发言管理双端验证')
class TestSpeechManagementDouble:
    """群管理-发言管理功能双端（群主发端与成员收端）协同验证测试

    核心业务规则：
    发言管理中，有些限制群主和管理员不受限制，只会限制普通成员。
    
    架构设计原则：
    1. 接收端常驻聊天页：接收方（普通成员/管理员）全程驻留群聊界面，零页面跳转成本。
    2. 发送端按需极速流转：群主端在群管理、发言管理与管理员列表之间单步直达，拒绝反复从主页重进。
    3. 防御式环境自治：用例结束后智能感知并重置发言管理配置与管理员身份，双端保底复原。

    5 大核心落地场景：
    1. 普通成员受限拦截（参数化典型消息类型）
    2. 管理员白名单豁免校验
    3. 身份降级即时受限校验
    4. 群主超级特权自发校验
    5. 总开关一键放行校验
    """

    mainS: MainPage
    chatListS: ChatListPage
    chatS: ChatPage
    groupSettingS: GroupSettingPage
    groupManagerS: GroupManagerPage
    groupBotS: GroupBotPage

    mainR: MainPage
    chatListR: ChatListPage
    chatR: ChatPage
    panelR: ChatPanelPage
    voicePageR: ChatVoicePage
    emojiPageR: ChatEmojiPage
    filePageR: ChatFilePage
    collectionR: ChatCollectionPage
    longPressR: ChatLongPressPage
    _is_admin_assigned: bool = False

    @pytest.fixture(autouse=True)
    def setup_double_env(self, driver_sender, driver_receiver):
        """初始化双端页面对象，双端进入目标群聊，用例结束后自动复原环境"""
        self._is_admin_assigned = False
        self.mainS = MainPage(driver_sender)
        self.chatListS = ChatListPage(driver_sender)
        self.chatS = ChatPage(driver_sender)
        self.groupSettingS = GroupSettingPage(driver_sender)
        self.groupManagerS = GroupManagerPage(driver_sender)
        self.groupBotS = GroupBotPage(driver_sender)

        self.mainR = MainPage(driver_receiver)
        self.chatListR = ChatListPage(driver_receiver)
        self.chatR = ChatPage(driver_receiver)
        self.panelR = ChatPanelPage(driver_receiver)
        self.voicePageR = ChatVoicePage(driver_receiver)
        self.emojiPageR = ChatEmojiPage(driver_receiver)
        self.filePageR = ChatFilePage(driver_receiver)
        self.collectionR = ChatCollectionPage(driver_receiver)
        self.longPressR = ChatLongPressPage(driver_receiver)

        with allure.step('-> [前置准备] 群主端与接收端进入目标群聊'):
            self.chatListS.enter_chat(GROUP_STRATEGY.name)
            self.chatS.wait_for_chat_page_load()
            self.chatListR.enter_chat(GROUP_STRATEGY.name)
            self.chatR.wait_for_chat_page_load()

        yield

        with allure.step('-> [环境清理] 复原发言管理开关与成员角色，双端安全返回主页'):
            try:
                self._safe_reset_group_manager_env()
            except Exception as e:
                logger.warning(f'⚠️ [Cleanup] 环境复原过程出现可忽略异常: {e}')
            finally:
                self.mainS.go_to_main_page()
                self.mainR.go_to_main_page()

    # =========================================================================
    # 极速轻量导航与状态安全重置辅助
    # =========================================================================
    def _ensure_in_group_manager(self) -> None:
        """确保群主端处于【群管理】页面（具备自愈与状态自适应能力）"""
        if self.groupManagerS.wait_for_group_manager_page_load(timeout=1, raise_exception=False):
            return

        if self.chatS.wait_for_chat_page_load(timeout=1, raise_exception=False):
            self.chatS.click_more_button()
            self.groupSettingS.wait_for_setting_page_load(timeout=2)
            self.groupSettingS.click_group_manager()
            self.groupManagerS.wait_for_group_manager_page_load()
            return

    def _open_speech_manage(self) -> None:
        """群主端进入【发言管理】页面"""
        self._ensure_in_group_manager()
        self.groupManagerS.click_speech_management()

    def _open_admin_manage(self) -> None:
        """群主端进入【管理员】列表页面"""
        self._ensure_in_group_manager()
        self.groupManagerS.click_administrators()
        self.groupManagerS.wait_for_admin_page_load()

    def _set_speech_limits(
        self,
        enable_master: bool = True,
        items: list[str] | None = None,
        all_items: bool = False,
    ) -> None:
        """群主端配置发言管理开关并保存（支持批量全开、指定单项与总开关控制）"""
        self._open_speech_manage()
        self.groupBotS.toggle_speech_manage_switch(enable=True)
        if all_items:
            self.groupBotS.toggle_all_limit_items(origin_enable=False, target_enable=True)
        elif items:
            for item in items:
                self.groupBotS.toggle_limit_item(item, enable=True)
        if not enable_master:
            self.groupBotS.toggle_speech_manage_switch(enable=False)
        self.groupBotS.click_save()

    def _assign_admin(self, user_name: str = PRIVATE_USER1.name) -> None:
        """群主端将指定成员设为管理员（幂等添加并记录标志位）"""
        self._open_admin_manage()
        existing_admins = self.groupManagerS.get_member_names()
        if user_name not in existing_admins:
            self.groupManagerS.click_add_admin()
            self.groupManagerS.click_member_by_name(name=user_name)
            self.groupManagerS.click_all_switch(checked_str='false')
            self.groupManagerS.click_confirm_button()
        self._is_admin_assigned = True

    def _remove_admin(self, user_name: str = PRIVATE_USER1.name) -> None:
        """群主端撤销指定成员的管理员身份并返回群管理页"""
        if not self.groupManagerS.wait_for_admin_page_load(timeout=1):
            self._open_admin_manage()
        names = self.groupManagerS.get_member_names()
        if user_name in names:
            logger.info(f"🔄 移除管理员身份: {user_name}")
            self.groupManagerS.click_member_by_name(name=user_name)
            self.groupManagerS.click_sure_button()
            self.groupManagerS.click_sure_content_button()
            self.groupManagerS.wait_for_admin_page_load(timeout=5)
        time.sleep(2)
        self._is_admin_assigned = False
        self.groupManagerS.click_iv_back_button()

    def _safe_reset_group_manager_env(self) -> None:
        """群主端环境统一安全复原：就近进入群管理，连续重置发言管理总开关与清理管理员身份"""
        self._ensure_in_group_manager()
        try:
            self.groupManagerS.click_speech_management()
            self.groupBotS.toggle_speech_manage_switch(enable=False)
            self.groupBotS.click_save()
        except Exception as e:
            logger.warning(f"⚠️ [Cleanup] 发言管理总开关重置异常: {e}")

        if getattr(self, '_is_admin_assigned', False):
            try:
                self._remove_admin(PRIVATE_USER1.name)
            except Exception as e:
                logger.warning(f"⚠️ [Cleanup] 管理员身份清理异常: {e}")

    @staticmethod
    def _assert_last_message_text(
        chat_page: ChatPage,
        expected_text: str,
        role_desc: str = "当前端",
        msg_type: str | None = None,
    ) -> None:
        """统一断言聊天窗口最后一条消息成功上屏且文本一致"""
        last_elem = chat_page.get_last_message_content_element(msg_type=msg_type)
        check.is_not_none(last_elem, f"❌ {role_desc}发送消息后未在上屏消息列表中找到该消息")
        if last_elem:
            check.equal(last_elem.text, expected_text, f"❌ {role_desc}发送文本内容不符合预期: {last_elem.text}")




    @allure.story('场景1：普通成员受限拦截')
    @allure.title('【普通成员拦截】群主开启全部限制后普通成员主动发送与长按传播全量拦截校验-状态：已完成')
    def test_member_speech_restrictions_blocked(self):
        """场景 1：普通成员全量受限拦截（高效批量校验）
        业务规则基线验证：群主一次性开启所有发言限制后，普通成员发起文本、表情、语音、面板扩展功能以及长按菜单传播全部被系统拦截。
        全量覆盖 14 类限制项：
        1. 主动发送限制（11项）：文本、表情、语音、图片、位置、群会议、名片、收藏、接龙、投票、文件；
        2. 二次传播限制（3项）：禁止复制群内消息、禁止转发群内消息、禁止保存/收藏群内消息。
        执行完成后群主端一次性复原环境，并校验接收端恢复正常发言能力。
        """
        with allure.step('1. 群主端进入发言管理，一次性开启总开关及所有子限制项并保存'):
            self._set_speech_limits(enable_master=True, all_items=True)

        with allure.step('2. 接收端（普通成员）依次发起各类交互，软断言校验被系统拦截'):
            with allure.step('2.1 校验【文本】发送拦截'):
                self.chatR.send_message("普通成员文本拦截测试")
                toast = self.chatR.get_toast()
                check.is_true("本群已开启禁止发送文本/emoji" in toast, f"❌ 【文本】拦截Toast不符合预期: '{toast}'")
                self.chatR.clear_input_text()

            with allure.step('2.2 校验【表情】发送拦截'):
                self.chatR.click_emoji_button()
                self.emojiPageR.sent_emoji(emoji_type="first")
                self.chatR.click_send_button()
                toast = self.chatR.get_toast()
                check.is_true("本群已开启禁止发送文本/emoji" in toast, f"❌ 【表情】拦截Toast不符合预期: '{toast}'")
                self.chatR.clear_input_text()

            with allure.step('2.3 校验【语音】发送拦截'):
                self.chatR.click_voice_button()
                self.voicePageR.click_voice_press_button()
                toast = self.chatR.get_toast()
                check.is_true("本群已开启禁止发送语音" in toast, f"❌ 【语音】拦截Toast不符合预期: '{toast}'")

            with allure.step('2.4 展开扩展面板，依次校验面板直点6大功能项拦截'):
                self.chatR.click_add_button()
                direct_panel_items = [
                    ("图片", "本群已开启禁止发送图片/拍照/视频"),
                    ("位置", "本群已开启禁止发送位置信息"),
                    ("群会议", "本群已开启禁止发起/参与音视频通话"),
                    ("名片", "本群已开启禁止发送个人/群名片"),
                    ("接龙", "本群已开启禁止发起接龙"),
                    ("投票", "本群已开启禁止发起投票"),
                ]
                for item_name, expected_toast in direct_panel_items:
                    with allure.step(f'校验面板项【{item_name}】拦截'):
                        self.panelR.click_panel_function_tab(item_name)
                        toast = self.chatR.get_toast()
                        check.is_true(expected_toast in toast, f"❌ 开启限制后【{item_name}】未捕获到预期拦截提示，实际 Toast: '{toast}'")

            with allure.step('2.5 校验通过【收藏】发送被系统拦截（防绕过）'):
                self.collectionR.open_panel_enter_collection_page()
                if self.collectionR.wait_for_collection_page_load(timeout=5):
                    self.collectionR.get_collection_text_and_click(index=0)
                    if self.collectionR.wait_for_send_collection_panel(timeout=3):
                        self.collectionR.click_send_collection_panel_send()
                toast = self.chatR.get_toast()
                allowed_toasts = ["本群已开启禁止发送文本/emoji", "本群已开启禁止发送图片/拍照/视频"]
                check.is_true(any(kw in toast for kw in allowed_toasts), f"❌ 发送收藏后未捕获到预期拦截提示，实际 Toast: '{toast}'")

            with allure.step('2.6 校验【发送文件】真实选择并发送被系统拦截'):
                self.filePageR.open_panel_enter_file_page()
                toast = self.chatR.get_toast()
                check.is_true("本群已开启禁止发送文件" in toast, f"❌ 发送文件后未捕获到预期拦截提示，实际 Toast: '{toast}'")
                self.chatR.click_add_button()

            with allure.step('2.7 校验消息二次传播扩散限制：长按群内消息【复制/转发/收藏】被系统拦截'):
                if not self.chatR.get_last_message_content_element():
                    self.chatS.send_message("群内消息长按传播限制测试基准")

                with allure.step('2.7.1 校验【禁止复制群内消息】拦截'):
                    self.longPressR.long_press_last_message(msg_type='text')
                    self.longPressR.click_copy()
                    toast = self.chatR.get_toast()
                    check.is_true("禁止复制群内消息" in toast, f"❌ 【复制】拦截提示不符合预期: '{toast}'")
                    time.sleep(0.3)

                with allure.step('2.7.2 校验【禁止转发群内消息】生效：长按菜单不展示【转发】按钮'):
                    self.longPressR.long_press_last_message(msg_type='text')
                    self.longPressR.wait_for_long_press_dialog()
                    is_forward_exist = self.longPressR.get_menu_item_status("转发")
                    check.is_false(is_forward_exist, "❌ 开启禁止转发后，长按菜单中依然展示了【转发】按钮")

                with allure.step('2.7.3 校验【禁止保存/收藏群内消息】拦截'):
                    has_fav = self.longPressR.get_menu_item_status("收藏")
                    if has_fav:
                        self.longPressR.click_favorite()
                        toast = self.chatR.get_toast()
                        check.is_true("本群已开启禁止保存/收藏群内消息" in toast, f"❌ 【收藏/保存】拦截提示不符合预期: '{toast}'")
                    else:
                        logger.info("✅ 开启限制后长按菜单未展示【收藏】入口，符合隐式权限拦截规则")

        with allure.step('3. 群主端关闭发言管理总开关解除限制'):
            self._open_speech_manage()
            self.groupBotS.toggle_speech_manage_switch(enable=False)
            self.groupBotS.click_save()

        with allure.step('4. 接收端校验限制解除后恢复正常发言能力'):
            test_msg = "限制解除后发言恢复测试"
            self.chatR.send_message(test_msg)
            self._assert_last_message_text(self.chatR, test_msg, "接收端")


    @allure.story('场景2：管理员白名单豁免校验')
    @allure.title('【管理员豁免】群主开启发言限制后管理员发送消息不受限制放行校验-状态：已完成')
    def test_admin_speech_restrictions_exemption(self):
        """场景 2：管理员白名单豁免校验
        核心业务规则验证：“发言管理中，有些限制群主和管理员不受限制，只会限制普通成员”。
        群主开启限制后，将普通成员提权为管理员；管理员在群内发送消息畅通无阻，消息正常上屏。
        双维度验证设计：
        1. 基础消息发送通道豁免（文本消息正常发出并上屏，无拦截提示）；
        2. 扩展面板直点功能豁免（音视频通话/群会议点击放行，不触发面板级拦截 Toast）。
        """
        test_msg = "管理员特权发送放行测试消息"

        with allure.step('1. 群主端进入发言管理开启总开关、文本限制及音视频通话限制并保存'):
            self._set_speech_limits(items=['文本', '音视频通话'])

        with allure.step('2. 群主端在群管理中将接收端设为管理员（幂等添加）'):
            self._assign_admin()

        with allure.step('3. 接收端（已是管理员）校验基础消息与扩展面板特权双向放行'):
            with allure.step('3.1 校验基础文本发送放行（无拦截Toast且正常上屏）'):
                self.chatR.send_message(test_msg)
                toast = self.chatR.get_toast(timeout=1)
                check.is_true("本群已开启禁止发送文本/emoji" not in toast, f"❌ 管理员发送文本被异常拦截: '{toast}'")
                self._assert_last_message_text(self.chatR, test_msg, "管理员")

            with allure.step('3.2 校验扩展面板直点功能放行（音视频通话/群会议不被拦截）'):
                self.chatR.click_add_button()
                self.panelR.click_panel_function_tab("群会议")
                panel_toast = self.chatR.get_toast(timeout=1)
                check.is_true("本群已开启禁止发起/参与音视频通话" not in panel_toast, f"❌ 管理员点击群会议被异常拦截: '{panel_toast}'")
                self.chatR.back_to_chat_page()
                
        with allure.step('4. 群主端移除管理员身份并退回群管理'):
            self._remove_admin()


    @allure.story('场景3：身份降级即时受限校验')
    @allure.title('【身份降级即时受限】管理员被撤职降为普通成员后发言限制立即生效校验-状态：已完成')
    def test_admin_demotion_instant_restriction(self):
        """场景 3：身份降级即时受限校验
        验证权限动态变更与即时生效：
        成员原为管理员时发言豁免，群主将其撤职降为普通成员后，发言限制立即生效，发送消息立即被拦截。
        """
        exempt_msg = "管理员豁免期验证消息"
        blocked_msg = "身份降级后拦截测试消息"
        expected_toast = "本群已开启禁止发送文本/emoji"

        with allure.step('1. 群主端进入发言管理开启文本限制并保存'):
            self._set_speech_limits(items=['文本'])

        with allure.step('2. 群主端在群管理中将接收端设为管理员（幂等添加）'):
            self._assign_admin()

        with allure.step('3. 接收端以管理员身份发言，确认豁免正常放行'):
            self.chatR.send_message(exempt_msg)
            toast = self.chatR.get_toast()
            check.is_true(expected_toast not in toast, f"❌ 管理员身份期发言被异常拦截: '{toast}'")
            self._assert_last_message_text(self.chatR, exempt_msg, "管理员")

        with allure.step('4. 群主端撤销接收端管理员身份（降级为普通成员）并退回群管理'):
            self._remove_admin()

        with allure.step('5. 降级后的接收端再次发送消息，校验发言限制立即生效拦截'):
            self.chatR.send_message(blocked_msg)
            toast = self.chatR.get_toast()
            check.is_true(expected_toast in toast, f"❌ 降级为普通成员后未触发预期发言拦截提示，实际 Toast: '{toast}'")


    @allure.story('场景4：群主超级特权自发校验')
    @allure.title('【群主超级特权】开启发言限制后群主自身发消息畅通无阻校验-状态：已完成')
    def test_owner_speech_restrictions_exemption(self):
        """场景 4：群主超级特权自发校验
        核心业务规则验证：群主拥有最高超级特权，开启发言限制后自身发消息畅通无阻，消息正常上屏并同步至接收端。
        """
        owner_msg = "群主最高超级权限自发测试消息"
        blocked_toast = "本群已开启禁止发送文本/emoji"

        with allure.step('1. 群主端进入发言管理开启总开关及文本限制并保存'):
            self._set_speech_limits(items=['文本'])

        with allure.step('2. 群主端顺畅退回群聊窗口发送消息'):
            self.chatS.back_to_chat_page()
            self.chatS.send_message(owner_msg)

        with allure.step('3. 校验群主端自身消息正常发出并上屏，且无拦截提示'):
            toast = self.chatS.get_toast()
            check.is_true(blocked_toast not in toast, f"❌ 群主自发消息异常触发发言拦截: '{toast}'")
            self._assert_last_message_text(self.chatS, owner_msg, "群主端", msg_type='text')

        with allure.step('4. 校验接收端正常接收群主发出的消息'):
            self._assert_last_message_text(self.chatR, owner_msg, "接收端", msg_type='text')


    @allure.story('场景5：总开关一键放行校验')
    @allure.title('【总开关一键放行】子项开启但总开关关闭时普通成员正常发言放行校验-状态：已完成')
    def test_speech_manage_master_switch_bypass(self):
        """场景 5：总开关一键放行校验
        验证发言管理总开关具有全局“一票否决/一票放行”控制力：
        子项（如文本限制）开关虽处于打开状态，但只要【发言管理】总开关处于关闭状态，限制规则不生效，普通成员发言畅通无阻。
        """
        test_msg = "总开关关闭子项开启放行测试"
        blocked_toast = "本群已开启禁止发送文本/emoji"

        with allure.step('1. 群主端进入发言管理，开启文本限制但关闭发言管理总开关并保存'):
            self._set_speech_limits(enable_master=False, items=['文本'])

        with allure.step('2. 接收端（普通成员）在群内发送文本消息'):
            self.chatR.send_message(test_msg)

        with allure.step('3. 校验总开关关闭时普通成员消息正常上屏，不受子项限制拦截'):
            toast = self.chatR.get_toast(timeout=1)
            check.is_true(blocked_toast not in toast, f"❌ 总开关关闭时发言被异常拦截，实际 Toast: '{toast}'")
            self._assert_last_message_text(self.chatR, test_msg, "普通成员", msg_type='text')
