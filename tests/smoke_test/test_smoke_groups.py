import pytest
import allure
import pytest_check as check
import time
from datetime import datetime
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.setting.chat_setting_page import ChatSettingPage
from pages.groups.create.group_create_page import GroupCreatePage
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.groups.setting.qrcode.group_qrcode_page import GroupQrCodePage
from pages.groups.setting.notice.group_notice_page import GroupNoticePage
from pages.groups.setting.manager.group_manager_page import GroupManagerPage
from pages.groups.setting.general.group_avatar_page import GroupAvatarPage
from pages.groups.bot.group_bot_page import GroupBotPage
from pages.common.contact_select_page import ContactSelectPage
from pages.common.session_select_page import SessionSelectPage
from pages.chat.core.chat_panel_page import ChatPanelPage
from pages.chat.core.chat_long_press_page import ChatLongPressPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2, GROUP_STRATEGY
from utils.cv_recognition.screenshot_utils import ImageComparator

class BaseSmokeGroupSingle:
    """群聊单端测试基类，收敛 Page 实例化及常用辅助方法"""

    @pytest.fixture(autouse=True)
    def setup_single(self, driver_sender):
        self.init_single_pages(driver_sender)
        yield
        try:
            self.mainPage.go_to_main_page()
        except Exception:
            pass

    def init_single_pages(self, driver):
        """显式初始化单端（及双端发送端）页面对象，确保 IDE 静态推导与跳转"""
        self.mainPage = MainPage(driver)
        self.homePage = HomePage(driver)
        self.groupCreatePage = GroupCreatePage(driver)
        self.groupSettingPage = GroupSettingPage(driver)
        self.groupQrCodePage = GroupQrCodePage(driver)
        self.groupManagerPage = GroupManagerPage(driver)
        self.groupAvatarPage = GroupAvatarPage(driver)
        self.groupBotPage = GroupBotPage(driver)
        self.chatPage = ChatPage(driver)
        self.chatListPage = ChatListPage(driver)
        self.contactSelectPage = ContactSelectPage(driver)
        self.chatSettingPage = ChatSettingPage(driver)
        self.groupNoticePage = GroupNoticePage(driver)
        self.selectPage = SessionSelectPage(driver)

    def init_receiver_pages(self, driver):
        """显式初始化双端接收端页面对象，确保 IDE 静态推导与跳转"""
        self.mainPageR = MainPage(driver)
        self.chatListPageR = ChatListPage(driver)
        self.chatPageR = ChatPage(driver)
        self.panelPageR = ChatPanelPage(driver)
        self.longPressPageR = ChatLongPressPage(driver)

    def _open_start_group_chat(self):
        """在首页点击加号并进入发起群聊页面"""
        self.homePage.click_add_button()
        self.homePage.click_start_group_chat()

    def _enter_group_setting(self):
        """进入群详情设置页"""
        self.chatListPage.enter_chat(GROUP_STRATEGY.name)
        self.chatPage.wait_for_chat_page_load(timeout=1, raise_exception=False)
        self.chatPage.click_more_button()
        self.groupSettingPage.wait_for_setting_page_load()




@allure.epic('IM核心功能测试')
@allure.feature('冒烟测试-群聊模块-创建与公告')
class TestSmokeGroupCreate(BaseSmokeGroupSingle):
    """群聊创建与群公告发布冒烟用例"""

    @pytest.mark.p0
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    @allure.story('群聊创建')
    @allure.title('通过首页右上角发起群聊 (小群:2人) - 正常建群流程-状态：已完成')
    def test_group_create_success(self):
        friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        expected_count = len(friend_list) + 1

        with allure.step('1. 进入发起群聊页面'):
            self._open_start_group_chat()

        with allure.step('2. 在通讯录列表中勾选多个好友并完成'):
            self.contactSelectPage.wait_for_contact_and_group_select_page_load()
            for contact in friend_list:
                self.contactSelectPage.click_contact_by_name(contact)
            self.contactSelectPage.click_action_button()

        with allure.step('3. 验证是否成功进入了群聊天页面'):
            is_in_chat = self.chatPage.wait_for_chat_page_load()
            check.is_true(is_in_chat, '❌ 建群后未能成功进入聊天页面')

        with allure.step('4. 验证群聊名称成功生成且非空'):
            group_name = self.chatPage.get_group_name()
            check.is_true(bool(group_name), f'❌ 获取群聊名称失败，实际为: {group_name}')

        with allure.step(f'5. 验证顶部独立群聊人数为 {expected_count} 人'):
            count = self.chatPage.get_group_number_count()
            check.equal(count, expected_count, f'❌ 群聊人数不为 {expected_count}，实际人数: {count}')

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.smoke
    @allure.story('群聊创建')
    @allure.title('通过好友发起群聊 - 取消建群流程-状态：已完成')
    def test_create_group_cancel(self):
        with allure.step('1. 进入好友聊天界面'):
            self.chatListPage.enter_session(PRIVATE_USER1.name, match_type='exact')
            is_in_chat = self.chatPage.wait_for_chat_page_load()
            check.is_true(is_in_chat, '❌ 未能成功进入聊天页面')

        with allure.step("2. 在聊天界面点击右上角'...' -> 添加成员"):
            self.chatPage.click_more_button()
            self.chatSettingPage.wait_for_setting_page_load()
            self.chatSettingPage.click_add_friend()

        with allure.step('3. 进入好友选择页后规范分层返回以取消建群'):
            is_select_page = self.contactSelectPage.wait_for_contact_and_group_select_page_load()
            check.is_true(is_select_page, '❌ 未能进入好友选择页')
            self.contactSelectPage.click_back()
            self.chatSettingPage.wait_for_setting_page_load()
            self.chatSettingPage.click_iv_back_button()

        with allure.step('4. 验证仍安全停留在原好友单聊页面'):
            is_in_chat = self.chatPage.wait_for_chat_page_load()
            check.is_true(is_in_chat, '❌ 取消建群后未能返回聊天页面')
            title = self.chatPage.get_top_name()
            check.is_in(PRIVATE_USER1.name, title, f'❌ 取消建群后聊天标题不正确，实际标题: {title}')
            check.is_false(self.groupCreatePage.is_chat_group(title), f'❌ 取消建群后不应进入群聊，实际标题: {title}')

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @allure.story('发布群公告')
    @allure.title('发布新群公告 - 正常发布流程-状态：已完成')
    def test_group_publish_notice_success(self):
        original_notice = ''
        new_notice = f"冒烟测试公告_{datetime.now().strftime('%m%d_%H%M%S')}"
        published = False

        try:
            with allure.step('1. 进入群聊并进入设置页'):
                self._enter_group_setting()

            with allure.step('2. 进入群公告并获取原公告'):
                raw_notice = self.groupNoticePage.get_notice_content()
                self.groupSettingPage.click_group_notice()
                self.groupNoticePage.wait_for_notice_page_load()
                original_notice = raw_notice if raw_notice else ''
                if original_notice:
                    self.groupNoticePage.click_publish_btn()

            with allure.step(f"3. 输入动态群公告内容并发布: '{new_notice}'"):
                self.groupNoticePage.input_notice_content(new_notice)
                self.groupNoticePage.click_publish_btn()
                published = True

            with allure.step('4. 验证群公告页面内容成功更新'):
                current_notice = self.groupNoticePage.get_notice_content()
                check.equal(current_notice, new_notice, f'❌ 发布后公告内容校验不一致，预期: {new_notice}, 实际: {current_notice}')

        finally:
            if published:
                with allure.step('5. 原地环境恢复：还原初始群公告'):
                    try:
                        if not self.groupNoticePage.wait_for_notice_page_load(timeout=1):
                            self.groupSettingPage.click_group_notice()
                            self.groupNoticePage.wait_for_notice_page_load()
                        self.groupNoticePage.click_publish_btn()
                        self.groupNoticePage.input_notice_content(original_notice)
                        self.groupNoticePage.click_publish_btn()
                    except Exception:
                        pass

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.smoke
    @allure.story('发布群公告')
    @allure.title('发布新群公告 - 取消发布流程-状态：已完成')
    def test_group_publish_notice_cancel(self):
        with allure.step('1. 进入群聊并进入设置页'):
            self._enter_group_setting()

        with allure.step('2. 进入群公告并开启编辑'):
            raw_desc = self.groupNoticePage.get_notice_content()
            self.groupSettingPage.click_group_notice()
            self.groupNoticePage.wait_for_notice_page_load()
            desc = raw_desc if raw_desc else ''
            if desc:
                self.groupNoticePage.click_publish_btn()

        with allure.step('3. 输入待测的群公告内容并点击返回取消'):
            notice_content = f"待取消公告_{datetime.now().strftime('%H%M%S')}"
            self.groupNoticePage.input_notice_content(notice_content)
            self.groupNoticePage.click_back_button()

        with allure.step('4. 验证公告内容未发生改变'):
            current_notice = self.groupNoticePage.get_notice_content() or ''
            check.equal(current_notice, desc, f'❌ 取消保存后，公告内容不应改变，预期为: {desc}, 实际为: {current_notice}')
            check.not_equal(current_notice, notice_content, '❌ 取消保存后，公告内容不应包含未保存的编辑内容')



@allure.epic('IM核心功能测试')
@allure.feature('冒烟测试-群聊模块-群管理设置')
class TestSmokeGroupManage(BaseSmokeGroupSingle):
    """群名称、头像、二维码以及成员管理等日常管理冒烟用例"""

    def _enter_group(self):
        self.chatListPage.enter_chat(GROUP_STRATEGY.name)
        self.chatPage.wait_for_chat_page_load(timeout=3, raise_exception=False)

    def _open_avatar_select_panel(self):
        self.groupAvatarPage.click_confirm_change_group_avatar()
        self.groupAvatarPage.wait_for_album_dialog()

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.smoke
    @allure.story('保存二维码')
    @allure.title('保存与分享群二维码功能-状态：已完成')
    def test_save_qrcode_success(self):
        with allure.step('1. 进入群聊并记录群名'):
            self._enter_group()
            group_name = self.chatPage.get_group_name()
        with allure.step('2. 进入群设置，并点击群二维码'):
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            self.groupSettingPage.click_group_qr_code()
            self.groupQrCodePage.wait_for_qrcode_page_load()
        with allure.step('3. 校验群二维码页面基础元素'):
            check.is_true(self.groupQrCodePage.is_qr_card_layout_visible(), '❌ 二维码卡片布局不可见')
            check.is_true(self.groupQrCodePage.is_group_header_visible(), '❌ 群头像未显示')
            check.is_true(self.groupQrCodePage.is_group_code_visible(), '❌ 二维码图片未渲染')
            group_name_on_card = self.groupQrCodePage.get_group_name()
            check.equal(group_name_on_card, group_name, '❌ 二维码卡片上显示的群名称与当前群聊不一致')
        with allure.step('4. 测试保存群二维码到本地'):
            self.groupQrCodePage.click_save_qrcode()
            toast = self.groupQrCodePage.get_toast()
            check.is_in('已保存到相册', toast, '❌ 保存二维码的提示信息有误')

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @allure.story('修改群名称')
    @allure.title('群聊名称修改校验-状态：已完成')
    def test_change_group_name_success(self):
        original_name = None
        new_name = f"群聊_{datetime.now().strftime('%m%d_%H%M%S')}"
        changed = False
        try:
            with allure.step('1. 进入群设置并记录原群名称'):
                self._enter_group_setting()
                original_name = self.groupSettingPage.get_nva_group_name()
                check.is_true(bool(original_name), '❌ 获取原群名称失败，无法执行修改校验')
            with allure.step(f"2. 触发修改群名称，输入动态名称: '{new_name}'"):
                self.groupSettingPage.click_group_name()
                is_dialog_loaded = self.groupSettingPage.wait_for_remark_dialog_load(nva_text='名称')
                check.is_true(is_dialog_loaded, '❌ 群名称编辑弹窗未加载')
                self.groupSettingPage.input_remark_content(new_name)
                self.groupSettingPage.click_tv_confirm_button()
            with allure.step('3. 校验修改后的群名称'):
                current_name = self.groupSettingPage.get_nva_group_name()
                check.equal(current_name, new_name, f"❌ 修改后的群聊名称与预期不符。预期: '{new_name}', 实际: '{current_name}'")
                changed = current_name == new_name
        finally:
            if changed and original_name:
                with allure.step('4. 环境重置为原始群名'):
                    try:
                        self.groupSettingPage.click_group_name()
                        self.groupSettingPage.wait_for_remark_dialog_load(nva_text='名称')
                        self.groupSettingPage.input_remark_content(original_name)
                        self.groupSettingPage.click_tv_confirm_button()
                        restored_name = self.groupSettingPage.get_nva_group_name()
                        check.equal(restored_name, original_name, f"❌ 群名称未恢复为原始值，实际: '{restored_name}'")
                    except Exception:
                        pass

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.smoke
    @allure.story('修改群头像')
    @allure.title('从相册修改群聊头像成功-状态：已完成')
    def test_modify_group_avatar_success(self):
        modified = False
        try:
            with allure.step('1. 进入群详情，并点击群头像进入大图预览'):
                self._enter_group_setting()
                self.groupAvatarPage.click_group_avatar()
                self.groupAvatarPage.wait_group_avatar_page_load()
                old_hash = self.groupAvatarPage.get_group_avatar_hash()
            with allure.step('2. 进入相册选择新头像'):
                self._open_avatar_select_panel()
                self.groupAvatarPage.click_group_avatar_pick_gallery()
                self.groupAvatarPage.wait_album_panel_load()
                self.groupAvatarPage.click_album_image_by_index(index=0)
                toast_text = self.groupAvatarPage.get_toast()
                check.equal('头像更新成功', toast_text, f'❌ 未弹出【头像更新成功】提示,实际:【{toast_text}】')
                self.groupAvatarPage.wait_group_avatar_page_load()
                modified = True
            with allure.step('3. 验证头像是否变更'):
                self.groupAvatarPage.click_back_to_group_setting()
                self.groupAvatarPage.click_group_avatar()
                self.groupAvatarPage.wait_group_avatar_page_load()
                new_hash = self.groupAvatarPage.get_group_avatar_hash()
                is_similar = ImageComparator.is_hash_similar(old_hash, new_hash, threshold=10)
                check.is_false(is_similar, '❌ 修改前后的群头像哈希相似度过高，群头像可能更新失败')
        finally:
            if modified:
                with allure.step('4. 环境安全重置原头像'):
                    try:
                        self._open_avatar_select_panel()
                        self.groupAvatarPage.click_group_avatar_pick_gallery()
                        self.groupAvatarPage.wait_album_panel_load()
                        self.groupAvatarPage.click_album_image_by_index(index=-1)
                        self.groupAvatarPage.wait_group_avatar_page_load()
                    except Exception:
                        pass

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @allure.story('群成员管理')
    @allure.title('群成员邀请与移除（踢人）流程-状态：已完成')
    def test_group_member_add_and_remove(self):
        """在已有群聊中，移出成员与重新邀请成员的闭环流程，异常安全还原"""
        removed = False
        init_count = 0
        try:
            with allure.step('1. 进入已有群聊设置页并获取当前成员数量基线'):
                self._enter_group_setting()
                init_count = self.groupSettingPage.get_group_member_number()
            with allure.step(f"2. 点击移除成员按钮，将好友 '{PRIVATE_USER1.name}' 移出群聊"):
                self.groupSettingPage.click_remove_friend_header()
                self.groupManagerPage.click_member_by_search_keyword(PRIVATE_USER1.name)
                self.groupManagerPage.click_edit_finish_button()
                self.chatPage.wait_banner_message_disappear()
                removed = True
            with allure.step('3. 原地校验群成员数量减少且被踢出的成员已不在列表中'):
                if init_count > 0:
                    current_count = self.groupSettingPage.get_group_member_number()
                    check.equal(current_count, init_count - 1, f'❌ 移除成员后群成员数量未减少 1 (期望: {init_count - 1}, 实际: {current_count})')
                current_members = self.groupSettingPage.get_friend_names()
                check.is_not_in(PRIVATE_USER1.name, current_members, f'❌ 好友 {PRIVATE_USER1.name} 仍存在于可见群成员列表中')
        finally:
            if removed:
                with allure.step(f"4. 环境恢复：重新邀请好友 '{PRIVATE_USER1.name}' 进群并校验人数还原"):
                    try:
                        self.groupSettingPage.click_add_friend_header()
                        self.groupManagerPage.click_member_by_search_keyword(PRIVATE_USER1.name)
                        self.groupManagerPage.click_edit_finish_button()
                        self.chatPage.wait_banner_message_disappear()
                        if init_count > 0:
                            restored_count = self.groupSettingPage.get_group_member_number()
                            check.equal(restored_count, init_count, f'❌ 恢复好友进群后群成员数量未还原 (期望: {init_count}, 实际: {restored_count})')
                    except Exception:
                        pass

    @pytest.mark.p0
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    @allure.story('解散群聊')
    @allure.title('通过群详情正常解散群聊流程-状态：已完成')
    def test_group_disband_success(self):
        """建临时群，执行解散群聊闭环流程"""
        friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        with allure.step('1. 在首页发起群聊创建临时群'):
            self._open_start_group_chat()
            self.contactSelectPage.wait_for_contact_and_group_select_page_load()
            for contact in friend_list:
                self.contactSelectPage.click_contact_by_name(contact)
            self.contactSelectPage.click_action_button()
            self.chatPage.wait_banner_message_disappear()
            self.chatPage.wait_for_chat_page_load()
        with allure.step('2. 进入群详情 -> 进入群管理 -> 点击解散群组'):
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            self.groupSettingPage.click_group_manager()
            self.groupManagerPage.wait_for_group_manager_page_load()
            self.groupManagerPage.click_dismiss_group()
        with allure.step('3. 确认弹窗解散群聊'):
            self.groupSettingPage.click_tv_confirm_button()
            toast = self.groupSettingPage.get_toast(expected_toast='解散成功')
            check.is_true(toast, '❌ 解散群聊后未弹出提示')
        with allure.step('4. 验证群聊解散后系统自动退回消息首页'):
            is_home_loaded = self.homePage.wait_home_page(timeout=10)
            check.is_true(is_home_loaded, '❌ 解散群聊后系统未能自动归位消息首页')




@allure.epic('IM核心功能测试')
@allure.feature('冒烟测试-群聊群管理模块-权限验证')
class TestSmokeGroupAdminDouble(BaseSmokeGroupSingle):
    """群聊日常管理（禁言、互相加好友、群管理员增删等）冒烟用例"""

    @pytest.fixture(autouse=True)
    def setup_method_fixture(self, setup_single):
        with allure.step('前置准备：进入目标群聊并进入群管理'):
            self.chatListPage.enter_chat(GROUP_STRATEGY.name)
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            self.groupSettingPage.click_group_manager()
            self.groupManagerPage.wait_for_group_manager_page_load()

    def _enter_group_setting_back(self):
        self.chatPage.click_more_button()
        self.groupSettingPage.wait_for_setting_page_load()

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @allure.story('群管理员增删')
    @allure.title('【群管理员】功能正常使用校验-状态：已完成')
    def test_group_manager_functionality(self):
        with allure.step('1. 点击群管理员，并添加管理员'):
            self.groupManagerPage.click_administrators()
            self.groupManagerPage.click_add_admin()
        with allure.step('2. 准备群管理员数据'):
            self.groupManagerPage.click_member_by_name(name=PRIVATE_USER1.name)
        with allure.step('3. 点击新增群管理员并确认'):
            self.groupManagerPage.click_all_switch(checked_str='false')
            self.groupManagerPage.click_confirm_button()
            self.chatPage.wait_banner_message_disappear()
        with allure.step('4. 返回管理员列表，并校验管理员状态'):
            member_names = self.groupManagerPage.get_member_names()
            check.is_in(PRIVATE_USER1.name, member_names, '❌ [Action-groupManagerPage] 添加管理员失败')
        with allure.step('5. 移除管理员'):
            self.groupManagerPage.click_member_by_name(name=PRIVATE_USER1.name)
            self.groupManagerPage.click_sure_button()
            self.groupManagerPage.click_sure_content_button()
            self.chatPage.wait_banner_message_disappear()
            member_names = self.groupManagerPage.get_member_names()
            check.is_not_in(PRIVATE_USER1.name, member_names, '❌ [Action-groupManagerPage] 移除管理员失败')

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @allure.story('禁言开关切换')
    @allure.title('切换【全员禁言】开关状态校验-状态：已完成')
    def test_all_member_mute_toggle(self):
        with allure.step('1. 开启全员禁言'):
            self.groupManagerPage.click_all_member_mute_switch(checked_str='true')
            self.chatPage.wait_banner_message_disappear()
        with allure.step('2. 回到聊天页面中，并校验全员禁言开启状态'):
            self.chatPage.back_to_chat_page()
            cmd_texts = self.chatPage.get_cmd_notification_texts(index=-1)
            check.is_in('开启全员禁言', cmd_texts, '❌ [Action-groupManagerPage] 全员禁言开关未开启')
        with allure.step('3. 再次点击开关恢复至初始状态'):
            self._enter_group_setting_back()
            self.groupSettingPage.click_group_manager()
            self.groupManagerPage.wait_for_group_manager_page_load()
            self.groupManagerPage.click_all_member_mute_switch(checked_str='false')
            self.chatPage.wait_banner_message_disappear()
        with allure.step('4. 回到聊天页面中，并校验全员禁言关闭后Banner消息'):
            self.chatPage.back_to_chat_page()
            cmd_texts = self.chatPage.get_cmd_notification_texts(index=-1)
            check.is_in('关闭全员禁言', cmd_texts, '❌ [Action-groupManagerPage] 全员禁言开关未关闭')

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @allure.story('群成员限制互加好友')
    @allure.title('切换【禁止群成员互相加好友】开关状态校验-状态：已完成')
    def test_un_add_friend_each_other_toggle(self):
        with allure.step('1. 开启禁止群成员互相加好友'):
            self.groupManagerPage.click_un_add_friend_each_other_switch(checked_str='true')
            self.chatPage.wait_banner_message_disappear()
        with allure.step('2. 回到聊天页面中，并校验禁止互相加好友开启状态'):
            self.chatPage.back_to_chat_page()
            cmd_texts = self.chatPage.get_cmd_notification_texts(index=-1)
            check.is_in('开启群禁止加好友', cmd_texts, '❌ [Action-groupManagerPage] 禁止群成员互相加好友开关未开启')
        with allure.step('3. 再次点击开关恢复至初始状态'):
            self._enter_group_setting_back()
            self.groupSettingPage.click_group_manager()
            self.groupManagerPage.wait_for_group_manager_page_load()
            self.groupManagerPage.click_un_add_friend_each_other_switch(checked_str='false')
            self.chatPage.wait_banner_message_disappear()
        with allure.step('4. 回到聊天页面中，并校验关闭后的Banner消息'):
            self.chatPage.back_to_chat_page()
            cmd_texts = self.chatPage.get_cmd_notification_texts(index=-1)
            check.is_in('关闭群禁止加好友', cmd_texts, '❌ [Action-groupManagerPage] 禁止群成员互相加好友开关未关闭')



@allure.epic('IM核心功能测试')
@allure.feature('冒烟测试-群聊模块-群机器人')
@pytest.mark.skip('TODO: 群机器人相关测试暂时跳过')
class TestSmokeGroupBot(BaseSmokeGroupSingle):
    """群聊机器人状态控制与交互冒烟用例"""

    @pytest.fixture(autouse=True)
    def setup_single(self, driver_sender, driver_receiver):
        """双端页面初始化与前台状态就绪（覆盖单端基类 fixture 避免重复 setup）"""
        self.init_single_pages(driver_sender)
        self.init_receiver_pages(driver_receiver)
        yield
        try:
            self.mainPage.go_to_main_page()
            self.mainPageR.go_to_main_page()
        except Exception:
            pass

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('关闭机器人发言限制')
    @allure.title('关闭群机器人发言管理总开关后，普通文本功能不再受限-状态：已完成')
    @pytest.mark.smoke
    def test_group_bot_disable_speech(self):
        """测试关闭机器人发言管理总开关后消息正常发送，并在 finally 中安全恢复开关"""
        need_restore = False
        try:
            with allure.step('1. 发送方进入群详情 -> 群设置 -> 群管理 -> 发言管理'):
                self.chatListPage.enter_chat(GROUP_STRATEGY.name)
                self.chatPage.wait_for_chat_page_load()
                self.chatPage.click_more_button()
                self.groupSettingPage.wait_for_setting_page_load()
                self.groupSettingPage.click_group_manager()
                self.groupManagerPage.wait_for_group_manager_page_load()
                self.groupManagerPage.click_speech_management()
            with allure.step('2. 发送方关闭发言管理总开关'):
                self.groupBotPage.toggle_speech_manage_switch(enable=False)
                self.groupBotPage.click_save()
                need_restore = True
            with allure.step('3. 接收方发送普通消息成功并上屏'):
                self.chatListPageR.enter_chat(GROUP_STRATEGY.name)
                self.chatPageR.wait_for_chat_page_load()
                test_msg = '机器人发言总开关关闭测试'
                self.chatPageR.send_message(test_msg)
                last_text = self.chatPageR.get_text_message_content_by_index(index=-1, side='sent')
                check.equal(last_text, test_msg, '❌ 发言管理关闭后，消息未能发送成功或内容不符')
        finally:
            if need_restore:
                with allure.step('4. 环境恢复：重新开启发言管理总开关'):
                    try:
                        self.groupBotPage.toggle_speech_manage_switch(enable=True)
                        self.groupBotPage.click_save()
                    except Exception:
                        pass

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('禁发关键词检测')
    @allure.title('开启禁发关键词检测后，发送敏感词被拦截撤回并展示警告-状态：已完成')
    @pytest.mark.smoke
    def test_group_bot_keyword_interception(self):
        """双端验证：配置禁发关键词后，违规消息被机器人撤回，并实现原地零冗余清理"""
        configured = False
        with allure.step('1. 发送方进入群详情 -> 群设置 -> 群助手 -> 禁发关键词'):
            self.chatListPage.enter_chat(GROUP_STRATEGY.name)
            self.chatPage.wait_for_chat_page_load()
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            self.groupSettingPage.click_friend_header()
            self.groupBotPage.wait_for_group_bot_page_load()
            self.groupBotPage.enter_keyword_block()
        try:
            with allure.step('2. 发送方开启禁发关键词总开关并添加敏感词'):
                self.groupBotPage.toggle_keyword_detection_switch(enable=True)
                self.groupBotPage.click_keyword_row()
                self.groupBotPage.set_keywords(['拦截测试'])
                self.groupBotPage.save_keywords_config()
                self.groupBotPage.click_save()
                configured = True
            with allure.step('3. 接收方在群聊内发送包含敏感词的消息'):
                self.chatListPageR.enter_chat(GROUP_STRATEGY.name)
                self.chatPageR.wait_for_chat_page_load()
                self.chatPageR.send_message('发送一条拦截测试消息')
            with allure.step('4. 接收方校验违规消息被群助手拦截并撤回'):
                withdraw_result = self.chatPageR.get_withdraw_message()
                check.is_not_none(withdraw_result, '❌ 发送敏感词后未被机器人撤回或未显示警告提示')
                if withdraw_result:
                    withdraw_msg, _ = withdraw_result
                    check.is_true('撤回' in withdraw_msg or '请勿发送' in withdraw_msg, f'❌ 撤回提示内容不匹配: {withdraw_msg}')
        finally:
            if configured:
                with allure.step('5. 环境清理：原地清空敏感词并关闭功能开关'):
                    try:
                        self.groupBotPage.click_keyword_row()
                        self.groupBotPage.clear_all_keywords()
                        self.groupBotPage.toggle_keyword_detection_switch(enable=False)
                        self.groupBotPage.click_save()
                    except Exception:
                        pass