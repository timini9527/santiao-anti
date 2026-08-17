import pytest
import allure
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.groups.create.group_create_page import GroupCreatePage
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.groups.setting.general.group_avatar_page import GroupAvatarPage
from pages.groups.setting.manager.group_manager_page import GroupManagerPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.common.contact_select_page import ContactSelectPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2, GROUP_STRATEGY, GROUP_STRATEGY2
from utils.cv_recognition.screenshot_utils import ImageComparator

@allure.epic('IM核心功能测试')
@allure.feature('群聊模块-群管理')
class TestGroupSetting:
    """群聊设置/群管理相关测试用例"""
    _has_entered_setting_page = False
    _initial_my_group_nickname = "__UNSET__"

    @pytest.fixture(autouse=True)
    def setup_class(self, request, driver_sender):
        """初始化页面对象并控制 Teardown 时机"""
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.groupCreatePage = GroupCreatePage(driver_sender)
        self.groupSettingPage = GroupSettingPage(driver_sender)
        self.groupAvatarPage = GroupAvatarPage(driver_sender)
        self.groupManagerPage = GroupManagerPage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        yield
        current_test_name = request.node.name
        should_go_home = False
        single_test_need_home = ['test_group_show_member_nickname_toggle', 'test_modify_my_group_nickname', 'test_delete_group_cancel', 'test_clear_group_chat_records']
        if any((name in current_test_name for name in single_test_need_home)):
            should_go_home = True
        elif 'test_group_remark_validation' in current_test_name and '超长20字限制截断' in current_test_name:
            should_go_home = True
        elif 'test_group_name_validation' in current_test_name and '群名称包含敏感词' in current_test_name:
            should_go_home = True
        if should_go_home:
            logger.info(f'🧹 [Teardown] 用例满足退回首页条件，执行 go_to_main_page: {current_test_name}')
            self.mainPage.go_to_main_page()
        else:
            logger.info(f'⏭️ [Teardown] 用例无需/已自行完成退回首页，略过 Teardown 回收: {current_test_name}')

    def _create_temp_group(self, friend_list):
        """内部辅助方法：快速创建一个用于测试的临时群聊"""
        with allure.step('-> [前置准备] 在首页发起群聊创建临时群'):
            self.homePage.click_add_button()
            self.homePage.click_start_group_chat()
            self.contactSelectPage.wait_for_contact_and_group_select_page_load()
            for contact in friend_list:
                self.contactSelectPage.click_contact_by_name(contact)
            self.contactSelectPage.click_action_button()
            self.chatPage.wait_banner_message_disappear()
            self.chatPage.wait_for_chat_page_load()

    def _create_group_and_go_to_dismiss(self, friend_list) -> str:
        """进入已建临时群并打开解散群聊确认界面"""
        with allure.step('-> [前置准备] 在首页发起群聊创建临时群'):
            self._create_temp_group(friend_list)
        with allure.step("2. 在群聊聊天页面点击右上角'...' -> 群设置"):
            self.chatPage.click_more_button()
            group_name = self.groupSettingPage.get_nva_group_name()
        with allure.step(f'3. 进入群详情页 -> {group_name}'):
            self.groupSettingPage.wait_for_setting_page_load()
            self.groupSettingPage.click_group_manager()
            self.groupManagerPage.click_dismiss_group()
        return group_name
    
    def _verify_group_disband(self, group_name):
        """验证群聊是否已解散"""
        self.chatListPage.enter_chat(group_name)
        self.chatPage.wait_for_chat_page_load()
        self.chatPage.click_more_button()
        toast = self.chatPage.get_toast_text()
        check.is_in('群不存在', toast, '❌ 群聊已被解散')
        self.groupSettingPage.click_quick_more()
        self.groupSettingPage.click_delete_and_out()
        self.groupSettingPage.click_tv_confirm_button()
    
    def _dismiss_and_cleanup_group(self, group_name: str):
        """执行确认解散、校验回首页并彻底清理失效会话"""
        with allure.step('-> [解散与清理] 确认解散群聊并销毁失效会话'):
            self.groupSettingPage.click_tv_confirm_button()
            toast = self.groupSettingPage.verify_toast_exist('解散成功')
            check.is_true(toast, '❌ 解散群聊后未弹出解散成功提示')
            title = self.homePage.get_top_middle_title(10)
            check.is_in('三条', title, '❌ 解散群聊后未能返回消息首页')
            self._verify_group_disband(group_name)


    def _enter_group_setting_page(self, group_name):
        """进入群设置页面 (使用内存 Flag 限制全局仅进入一次)"""
        if getattr(self.__class__, '_has_entered_setting_page', False):
            logger.info('⚡ [Setup] 当前已在群聊设置页，跳过重复进入流程')
            return
        with allure.step('1. 进入群设置页面'):
            self.chatListPage.enter_chat(group_name)
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            self.__class__._has_entered_setting_page = True

    @allure.story('群聊详情设置')
    @allure.title('切换显示群成员昵称开关并校验状态-状态：已完成')
    def test_group_show_member_nickname_toggle(self):
        """测试显示群成员昵称开关状态切换与恢复"""
        with allure.step('1. 进入群设置页面'):
            self.chatListPage.enter_chat(GROUP_STRATEGY.name)
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
        with allure.step('2. 获取当前显示群成员昵称状态'):
            init_state = self.groupSettingPage.get_show_member_name_switch_state()
        with allure.step('3. 点击显示群成员昵称进行切换'):
            self.groupSettingPage.click_show_member_name_switch()
            new_state = self.groupSettingPage.get_show_member_name_switch_state()
            check.not_equal(init_state, new_state, '❌ 显示群成员昵称开关切换失败')
        with allure.step('4. 再次点击恢复初始状态'):
            self.groupSettingPage.click_show_member_name_switch()
            final_state = self.groupSettingPage.get_show_member_name_switch_state()
            check.equal(init_state, final_state, '❌ 显示群成员昵称开关恢复初始状态失败')

    @allure.story('群聊详情设置')
    @allure.title('修改‘我在本群昵称’并校验修改成功-状态：已完成')
    def test_modify_my_group_nickname(self):
        """测试修改我在本群的昵称并安全恢复"""
        with allure.step('1. 进入群设置页面'):
            self.chatListPage.enter_chat(GROUP_STRATEGY.name)
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
        with allure.step('2. 获取修改前的群内昵称值'):
            old_nickname = self.groupSettingPage.get_my_group_nickname()
        with allure.step('3. 输入新昵称并确认保存'):
            target_nickname = '自动化测试群昵称'
            self.groupSettingPage.change_my_group_nickname(target_nickname)
        with allure.step('4. 校验群内昵称是否更新成功'):
            new_nickname = self.groupSettingPage.get_my_group_nickname()
            check.equal(new_nickname, target_nickname, '❌ 我在本群昵称修改值不一致')
        with allure.step('5. 恢复初始群内昵称值'):
            restore_nickname = old_nickname if old_nickname else ''
            self.groupSettingPage.change_my_group_nickname(restore_nickname)
            check.equal(self.groupSettingPage.get_my_group_nickname(), old_nickname, '❌ 我在本群昵称恢复值不一致')

    @allure.story('解散群聊')
    @allure.title('通过群聊聊天页面解散群聊 - 正常解散流程-状态：已完成')
    def test_delete_group_success(self):
        allure.dynamic.description(f'通过群聊聊天页面解散群聊')
        friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        group_name = self._create_group_and_go_to_dismiss(friend_list)
        with allure.step('3. 确认弹窗'):
            self._dismiss_and_cleanup_group(group_name)

    @allure.story('解散群聊')
    @allure.title('通过群聊聊天页面解散群聊 - 取消解散流程-状态：已完成')
    def test_delete_group_cancel(self):
        """验证群主点击解散群聊后选择取消，群聊保持正常，并在最后完成清理"""
        allure.dynamic.description('通过群聊聊天页面解散群聊 - 取消解散流程')
        friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        group_name = self._create_group_and_go_to_dismiss(friend_list)
        try:
            with allure.step('4. 取消解散群聊确认'):
                self.groupSettingPage.click_tv_cancel_button()
            with allure.step('5. 逐级返回群聊聊天页面'):
                self.groupManagerPage.click_iv_back_button()
                self.groupSettingPage.click_iv_back_button()
                self.chatPage.wait_for_chat_page_load()
                title = self.chatPage.get_top_name()
                check.is_true(bool(title), '❌ 取消解散后未能正确返回群聊页面')
            with allure.step('6. 校验群聊未被解散，仍可正常发送消息'):
                self.chatPage.send_message('取消解散群聊验证')
        finally:
            with allure.step('-> [Teardown] 销毁清理临时群聊数据'):
                self.chatPage.click_more_button()
                self.groupSettingPage.wait_for_setting_page_load()
                self.groupSettingPage.click_group_manager()
                self.groupManagerPage.click_dismiss_group()
                self._dismiss_and_cleanup_group(group_name)


    @allure.story('群聊设置 - 清空聊天记录')
    @allure.title('清空群聊聊天记录并校验记录归零-状态：已完成')
    @pytest.mark.parametrize('chat_strategy', [pytest.param(GROUP_STRATEGY2, id='群聊-清空聊天记录')])
    def test_clear_group_chat_records(self, chat_strategy):
        """进入群聊发送消息，通过群详情更多操作清空聊天记录，并校验聊天界面消息被清空"""
        allure.dynamic.title(f'{chat_strategy.name} - 清空聊天记录')
        with allure.step(f'1. 进入群聊会话【{chat_strategy.name}】并发送测试消息'):
            self.chatListPage.enter_chat(chat_strategy.name)
            self.chatPage.wait_for_chat_page_load()
            self.chatPage.send_message('测试清空群聊天记录功能')
        with allure.step('2. 获取当前群聊天页面的消息总数'):
            msg_count = self.chatPage.get_total_message_count()
            check.is_true(msg_count > 0, f'❌ 发送消息后，聊天页面消息总数应大于 0，实际为 {msg_count}')
        with allure.step('3. 进入群详情设置页'):
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
        with allure.step('4. 点击【更多】->【清空聊天记录】并确认弹窗'):
            self.groupSettingPage.click_quick_more()
            self.groupSettingPage.click_clear_group_chat_message()
            self.groupSettingPage.click_tv_confirm_button()
            self.groupSettingPage.click_iv_back_button()
        with allure.step('5. 校验返回聊天页面后消息记录已全部清空'):
            self.chatPage.wait_for_chat_page_load()
            new_msg_count = self.chatPage.get_total_message_count()
            check.equal(new_msg_count, 0, f'❌ 清空聊天记录后，消息数量应为 0，实际为 {new_msg_count}')

    @allure.story('群备注功能')
    @allure.title('群备注修改校验 - {test_id}-状态：已完成')
    @pytest.mark.parametrize('test_id, input_content, action, expected_toast, expect_truncated, should_change, last_case', [
        pytest.param('正常修改并保存', '测试群备注1', 'confirm', '', False, True, False, id='正常修改并保存'),
        pytest.param('敏感词拦截', '习近平', 'confirm', '群备注名不合法，请换个群备注名', False, False, False, id='敏感词拦截'),
        pytest.param('修改并取消', '企图修改备注但取消', 'cancel', '', False, False, False, id='修改并取消'),
        pytest.param('超长20字限制截断', '一二三四五六七八九十一二三四五六七八九十加', 'confirm', '', True, True, True, id='超长20字限制截断')
    ])
    @pytest.mark.parametrize('chat_strategy', [pytest.param(GROUP_STRATEGY, id='群聊-群备注功能')])
    def test_group_remark_validation(self, test_id, input_content, action, expected_toast, expect_truncated, should_change, last_case, chat_strategy):
        """测试不同场景下的群备注修改逻辑（保存、取消、敏感词拦截、超长20字限制截断与安全恢复）"""
        self._enter_group_setting_page(chat_strategy.name)
        with allure.step('2. 获取修改前的群备注'):
            old_remark = self.groupSettingPage.get_group_remark()
        with allure.step(f"3. 点击群备注，输入待测内容: '{input_content}' 并执行【{action}】"):
            self.groupSettingPage.click_group_remark()
            is_dialog = self.groupSettingPage.wait_for_remark_dialog_load(nva_text='群备注')
            check.is_true(is_dialog, '❌ 群备注编辑弹窗未加载')
            self.groupSettingPage.input_remark_content(input_content)
            if action == 'confirm':
                self.groupSettingPage.click_tv_confirm_button()
            else:
                self.groupSettingPage.click_tv_cancel_button()
        with allure.step('4. 校验修改后的群备注结果与提示'):
            if expected_toast:
                toast = self.groupSettingPage.get_toast()
                check.is_in(expected_toast, toast, f"❌ 未能监测到预期的 Toast 提示: '{expected_toast}', 实际: '{toast}'")
                if self.groupSettingPage.wait_for_remark_dialog_load(nva_text='群备注'):
                    self.groupSettingPage.click_tv_cancel_button()
            if not should_change:
                new_remark = self.groupSettingPage.get_group_remark()
                check.equal(new_remark, old_remark, '❌ 异常操作或取消后，群备注发生意外变更')
            else:
                new_remark = self.groupSettingPage.get_group_remark()
                expected_remark = input_content[:20] if expect_truncated else input_content
                check.equal(new_remark, expected_remark, f"❌ 群备注修改后与预期不符。预期: '{expected_remark}', 实际: '{new_remark}'")
        with allure.step('5. 恢复初始群备注值'):
            if last_case:
                self.groupSettingPage.click_group_remark()
                self.groupSettingPage.wait_for_remark_dialog_load(nva_text='群备注')
                self.groupSettingPage.input_remark_content('')
                self.groupSettingPage.click_tv_confirm_button()

    @allure.story('群名称功能')
    @allure.title('群聊名称修改校验 - {scenario}-状态：已完成')
    @pytest.mark.parametrize('scenario, input_name, action, expected_toast, expected_result, should_change, last_case', [
        pytest.param('empty', '', 'confirm', '群名称不能为空', '', False, False, id='群名称设置为空'),
        pytest.param('success', '新群聊名称', 'confirm', '', '新群聊名称', True, False, id='群名称正常修改'),
        pytest.param('cancel', '企图修改群名称但取消', 'cancel', '', '', False, False, id='修改群名称并取消'),
        pytest.param('limit_20', '一二三四五六七八九十一二三四五六七八九十', 'confirm', '', '一二三四五六七八九十一二三四五六七八九十', True, False, id='群名称上限20个字'),
        pytest.param('limit_20_over', '一二三四五六七八九十一二三四五六七八九十超限', 'confirm', '', '一二三四五六七八九十一二三四五六七八九十', True, False, id='群名称超限20字截断'),
        pytest.param('sensitive', '习近平', 'confirm', '操作不成功，请换个名称！', '', False, True, id='群名称包含敏感词')
    ])
    @pytest.mark.parametrize('chat_strategy', [pytest.param(GROUP_STRATEGY, id='群聊-群名称功能')])
    def test_group_name_validation(self, scenario, input_name, action, expected_toast, expected_result, should_change, last_case, chat_strategy):
        """验证群聊名称的修改规则，包含空输入、字数上限20个字截断、敏感词拦截、取消修改与环境恢复"""
        self._enter_group_setting_page(chat_strategy.name)
        with allure.step('2. 获取修改前的群名称'):
            old_group_name = self.groupSettingPage.get_nva_group_name()
        with allure.step(f"3. 触发修改群名称，输入: '{input_name}' 并执行【{action}】"):
            self.groupSettingPage.click_group_name()
            is_dialog = self.groupSettingPage.wait_for_remark_dialog_load(nva_text='群聊名称')
            check.is_true(is_dialog, '❌ 群名称编辑弹窗未加载')
            self.groupSettingPage.input_remark_content(input_name)
            if action == 'confirm':
                self.groupSettingPage.click_tv_confirm_button()
            else:
                self.groupSettingPage.click_tv_cancel_button()
        with allure.step('4. 校验修改后的结果与提示'):
            if expected_toast:
                toast_text = self.groupSettingPage.get_toast()
                check.is_in(expected_toast, toast_text, f"❌ 未能监测到预期的 Toast 提示: '{expected_toast}', 实际: '{toast_text}'")
                if self.groupSettingPage.wait_for_remark_dialog_load(nva_text='群聊名称'):
                    self.groupSettingPage.click_tv_cancel_button()
            if not should_change:
                current_name = self.groupSettingPage.get_nva_group_name()
                check.equal(current_name, old_group_name, '❌ 异常输入或取消后，群聊名称意外发生了改变')
            else:
                current_name = self.groupSettingPage.get_nva_group_name()
                check.equal(current_name, expected_result, f"❌ 修改后的群聊名称与预期不符。预期: '{expected_result}', 实际: '{current_name}'")
        with allure.step('5. 恢复初始群名称'):
            if last_case:
                self.groupSettingPage.click_group_name()
                self.groupSettingPage.wait_for_remark_dialog_load(nva_text='群聊名称')
                self.groupSettingPage.input_remark_content(chat_strategy.name)
                self.groupSettingPage.click_tv_confirm_button()

    @allure.story('群设置-群头像')
    @allure.title('通过群聊聊天页面修改群头像-状态：已完成')
    def test_change_group_avatar(self):
        """建临时群进入大图预览，从相册修改群头像，校验哈希变动后解散群聊清理环境"""
        friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        self._create_temp_group(friend_list)
        try:
            with allure.step('1. 进入群设置页面与群头像大图预览'):
                self.chatPage.click_more_button()
                self.groupSettingPage.wait_for_setting_page_load()
                group_name = self.groupSettingPage.get_nva_group_name()
                self.groupAvatarPage.click_group_avatar()
                self.groupAvatarPage.wait_group_avatar_page_load()
                old_hash = self.groupAvatarPage.get_group_avatar_hash()
            with allure.step('2. 打开修改面板，从相册选择新头像并保存'):
                self.groupAvatarPage.click_confirm_change_group_avatar()
                self.groupAvatarPage.wait_for_album_dialog()
                self.groupAvatarPage.click_group_avatar_pick_gallery()
                self.groupAvatarPage.wait_album_panel_load()
                self.groupAvatarPage.click_album_image_by_index(index=0)
                toast_text = self.groupAvatarPage.get_toast()
                check.equal('头像更新成功', toast_text, f'❌ 未弹出【头像更新成功】提示，实际:【{toast_text}】')
                self.groupAvatarPage.wait_group_avatar_page_load()
            with allure.step('3. 校验群头像哈希已发生物理变更'):
                self.groupAvatarPage.click_back_to_group_setting()
                self.groupAvatarPage.click_group_avatar()
                new_hash = self.groupAvatarPage.get_group_avatar_hash()
                is_similar = ImageComparator.is_hash_similar(old_hash, new_hash, threshold=10)
                check.is_false(is_similar, '❌ 修改前后的群头像哈希相似度过高，群头像可能更新失败')
                self.groupAvatarPage.click_back_to_group_setting()
        finally:
            with allure.step('-> [Teardown] 解散临时群聊并清理会话'):
                self.groupSettingPage.click_group_manager()
                self.groupManagerPage.click_dismiss_group()
                self._dismiss_and_cleanup_group(group_name)

    @allure.story('群设置-我在本群昵称')
    @allure.title('我在本群昵称修改校验 - {scenario}-状态：已完成')
    @pytest.mark.parametrize('scenario, input_nickname, action, expected_result, should_change, last_case', [
        pytest.param('success', '自动化群昵称', 'confirm', '自动化群昵称', True, False, id='我在本群昵称正常修改'),
        pytest.param('cancel', '企图修改昵称但取消', 'cancel', '', False, False, id='我在本群昵称取消修改'),
        pytest.param('limit_10', '1234567890', 'confirm', '1234567890', True, False, id='我在本群昵称上限10字'),
        pytest.param('limit_over', '一二三四五六七八九十一二', 'confirm', '一二三四五六七八九十', True, False, id='我在本群昵称超限10字截断'),
        pytest.param('sensitive', '习近平', 'confirm', '', False, True, id='我在本群昵称敏感词拦截')
    ])
    @pytest.mark.parametrize('chat_strategy', [pytest.param(GROUP_STRATEGY, id='群聊-我在本群昵称')])
    def test_group_nickname_validation(self, scenario, input_nickname, action, expected_result, should_change, last_case, chat_strategy):
        """测试不同场景下修改我在本群昵称（保存、取消、字数上限10字、敏感词拦截与环境安全恢复）"""
        self._enter_group_setting_page(chat_strategy.name)
        with allure.step('2. 获取修改前的群内昵称'):
            old_nickname = self.groupSettingPage.get_my_group_nickname()
            if self.__class__._initial_my_group_nickname == "__UNSET__":
                self.__class__._initial_my_group_nickname = old_nickname
        with allure.step(f"3. 触发修改我在本群昵称，输入: '{input_nickname}' 并执行【{action}】"):
            self.groupSettingPage.change_my_group_nickname(input_nickname, action=action)
        with allure.step('4. 校验修改后的结果与弹窗清理'):
            if self.groupSettingPage.wait_for_remark_dialog_load(nva_text='本群昵称'):
                self.groupSettingPage.click_tv_cancel_button()
            current_nickname = self.groupSettingPage.get_my_group_nickname()
            if not should_change:
                check.equal(current_nickname, old_nickname, '❌ 异常输入或取消后，我在本群昵称意外发生了改变')
            else:
                check.equal(current_nickname, expected_result, f"❌ 修改后的群内昵称与预期不符。预期: '{expected_result}', 实际: '{current_nickname}'")
        with allure.step('5. 恢复初始群内昵称'):
            if last_case:
                restore_val = self.__class__._initial_my_group_nickname if self.__class__._initial_my_group_nickname != "__UNSET__" else ""
                self.groupSettingPage.change_my_group_nickname(restore_val)
                self.__class__._initial_my_group_nickname = "__UNSET__"

    @allure.story('群设置-显示群成员昵称')
    @allure.title('开启显示群成员昵称并校验聊天页昵称展示-状态：已完成')
    def test_group_display_member_nickname(self):
        """进入群设置开启显示群成员昵称开关，返回聊天页校验昵称元素可见，并在最后恢复开关状态"""
        with allure.step('1. 进入群设置页面'):
            self.chatListPage.enter_chat(GROUP_STRATEGY.name)
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
        with allure.step('2. 记录初始状态并将开关设置为开启'):
            init_state = self.groupSettingPage.get_show_member_name_switch_state()
            self.groupSettingPage.click_show_member_name_switch(target_state=True)
        try:
            with allure.step('3. 返回群聊天页面'):
                self.groupSettingPage.click_iv_back_button()
                self.chatPage.wait_for_chat_page_load()
            with allure.step('4. 校验聊天界面中群成员昵称元素正常展示'):
                user_name_elements = self.chatPage.get_group_chat_user_name_elements()
                check.is_true(len(user_name_elements) > 0, '❌ 开启开关后聊天界面未展示群成员昵称')
        finally:
            with allure.step('-> [Teardown] 恢复显示群成员昵称初始开关状态'):
                self.chatPage.click_more_button()
                self.groupSettingPage.wait_for_setting_page_load()
                self.groupSettingPage.click_show_member_name_switch(target_state=init_state)
                self.groupSettingPage.click_iv_back_button()


    @allure.story('群设置-消息免打扰')
    @allure.title('切换消息免打扰开关状态并校验-状态：未完成')
    @pytest.mark.skip(reason="切换消息免打扰开关状态并校验-状态：未完成")
    def test_group_dnd_toggle(self):
        """测试群详情消息免打扰开关的切换与状态恢复"""
        with allure.step('1. 进入群设置页面'):
            self.chatListPage.enter_chat(GROUP_STRATEGY.name)
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
        with allure.step('2. 修改群设置-成员进群提醒'):
            pass
        with allure.step('3. 校验群设置-成员进群提醒'):
            pass