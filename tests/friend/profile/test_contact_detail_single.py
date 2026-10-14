import time
import allure
import pytest
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.friend.profile.contact_detail_page import ContactDetailPage
from pages.common.contact_select_page import ContactSelectPage
from pages.friend.profile.remark_setting_page import RemarkSettingPage
from pages.chat.core.chat_page import ChatPage
from pages.friend.tag_group.contact_tag_group_page import ContactTagGroupPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER3




SENDER_NAME = PRIVATE_USER3.name
RECEIVER_NAME = PRIVATE_USER1.name

@allure.epic('IM核心功能测试')
@allure.feature('好友资料模块')
@allure.story('好友资料卡展示与备注设置(单端)')
class TestContactDetailSingle:
    """单端好友资料详情管理与备注设置测试集 (仅操作发送端，提速运行)"""

    @pytest.fixture(scope='class', autouse=True)
    def setup_class_nav(self, driver_sender):
        """类级别前置：全类仅执行1次，从主页展开底栏并进入好友/通讯录列表页"""
        main_page = MainPage(driver_sender)
        home_page = HomePage(driver_sender)
        main_page.go_to_main_page()
        home_page.click_bottom_expand_button()
        home_page.click_friend()
        home_page.wait_for_friend_page_load()
        yield
        main_page.go_to_main_page()

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender, request):
        """用例级别前置与后置：初始化页面对象，后置确保停留在对应页面"""
        self.mainPageS = MainPage(driver_sender)
        self.homePageS = HomePage(driver_sender)
        self.contactSelectPageS = ContactSelectPage(driver_sender)
        self.contactDetailPageS = ContactDetailPage(driver_sender)
        self.remarkSettingPageS = RemarkSettingPage(driver_sender)
        self.chatPageS = ChatPage(driver_sender)
        self.tagGroupPageS = ContactTagGroupPage(driver_sender)
        yield
        test_name = request.node.name
        is_remark_test = 'remark' in test_name
        try:
            if is_remark_test:
                if not self.homePageS.wait_for_friend_page_load(timeout=2):
                    if self.contactDetailPageS.wait_for_detail_page_load(timeout=2):
                        self.contactDetailPageS.click_iv_back()
                    self.homePageS.click_friend()
            elif not self.contactDetailPageS.wait_for_detail_page_load(timeout=1, raise_exception=False):
                if not self.homePageS.wait_for_friend_page_load(timeout=1):
                    self.contactDetailPageS.click_iv_back()
        except Exception as e:
            logger.error(f'⚠️ [Teardown] 页面状态恢复失败: {e}')

    def _click_contact_by_name(self, name: str, raise_exception: bool=True, search: bool=False) -> bool:
        """点击通讯录好友并等待详情页加载完成"""
        click_ok = self.contactSelectPageS.click_contact_by_name(name, raise_exception=raise_exception, search=search)
        if click_ok:
            self.contactDetailPageS.wait_for_detail_page_load(timeout=8)
        return click_ok

    def _go_to_contact_detail_from_list(self, name: str, raise_exception: bool=False) -> bool:
        """导航辅助方法：在通讯录列表中查找并进入指定好友的资料详情页。如果已在目标好友详情页，则跳过列表查找。"""
        try:
            if self.contactDetailPageS.wait_for_detail_page_load(timeout=1, raise_exception=raise_exception):
                current_name = self.contactDetailPageS.get_formatted_friend_name()
                if current_name == name:
                    logger.info(f'✨ [Lock] 已在好友 {name} 的资料页，跳过列表查找直接开始测试步骤')
                    return True
                self.contactDetailPageS.click_iv_back()
                self.homePageS.wait_for_friend_page_load()
        except Exception as e:
            logger.warning(f'⚠️ 预检好友详情页状态时发生异常 (将退回列表重新查找): {e}')
        return self._click_contact_by_name(name, raise_exception=raise_exception)

    def _go_to_remark_setting_page(self, name: str=RECEIVER_NAME):
        """通用步骤：进入好友资料详情页并进入设置备注页"""
        self._go_to_contact_detail_from_list(name)
        self.contactDetailPageS.click_friend_detail_title_remark()
        self.remarkSettingPageS.wait_friend_detail_page()

    def _prepare_tag_page_and_clean(self):
        """通用步骤：进入好友资料卡 -> 设置备注页 -> 标签页 -> 清理已选中的标签"""
        self._go_to_remark_setting_page()
        tag_values = self.remarkSettingPageS.get_tag_values()
        self.remarkSettingPageS.click_tags()
        self.remarkSettingPageS.wait_for_tag_page_load()
        if tag_values:
            self.remarkSettingPageS.clear_tag(list_tags=tag_values)

    def _clean_tags_and_back_to_detail(self):
        """通用步骤：在标签页/备注页清理已选标签并安全切回好友详情页"""
        self.contactDetailPageS.click_friend_detail_title_remark()
        self.remarkSettingPageS.wait_friend_detail_page()
        tag_values = self.remarkSettingPageS.get_tag_values()
        if tag_values:
            self.remarkSettingPageS.click_tags()
            self.remarkSettingPageS.wait_for_tag_page_load()
            self.remarkSettingPageS.clear_tag(list_tags=tag_values)
            self.remarkSettingPageS.wait_friend_detail_page()
        self.contactDetailPageS.click_iv_back()

    def _go_to_phone_setting_page(self):
        """通用步骤：进入好友资料卡 -> 点击设置备注 -> 进入电话列表项"""
        self._go_to_remark_setting_page()
        self.remarkSettingPageS.click_phone_item()

    def _cancel_from_tag_search_to_detail(self):
        """通用导航步骤：从已搜索标签状态的标签页，逐级退出并安全返回到好友资料卡详情页"""
        with allure.step('1. 退出tag页面'):
            self.remarkSettingPageS.click_tv_cancel()
        with allure.step('2. 退出编辑备注页面'):
            self.remarkSettingPageS.click_tv_cancel()
        with allure.step('3. 确认放弃修改'):
            self.contactDetailPageS.cancel_two_btn_comment()
        with allure.step('4. 等待返回到设置备注主页'):
            self.remarkSettingPageS.wait_friend_detail_page()
        with allure.step('5. 从备注页返回至好友资料详情页'):
            self.contactDetailPageS.click_iv_back()
        with allure.step('6. 确认详情页加载完成'):
            self.contactDetailPageS.wait_for_detail_page_load()

    def _clear_all_tags(self):
        """通用步骤：进入好友页面-分组管理-删除所有分组"""
        with allure.step('1. 进入分组管理页面'):
            self.homePageS.click_category_manager()
            self.tagGroupPageS.wait_for_group_list_page_load(page_title='0')
            group_names = self.tagGroupPageS.get_group_tag_names(timeout=1, raise_exception=False)
            if not group_names:
                logger.info('✅ [Action - TagGroup] 分组管理页面分组已全部删除，无需再操作')
                self.contactDetailPageS.click_iv_back()
                return
        with allure.step('2. 执行批量清空所有分组操作'):
            del_all_result = self.tagGroupPageS.delete_group_or_all_groups_flow(is_all=True)
            check.is_true(del_all_result, '❌ 批量清空所有分组流执行失败')
        with allure.step('3. 校验列表是否已完全清空'):
            self.tagGroupPageS.wait_for_group_list_page_load(page_title='0')
            remaining_names = self.tagGroupPageS.get_group_tag_names(timeout=1, raise_exception=False)
            check.equal(len(remaining_names), 0, f'❌ 批量删除后列表中依然残留分组: {remaining_names}')
        with allure.step('4. 返回好友资料详情页'):
            self.contactDetailPageS.click_iv_back()
            self.homePageS.wait_for_friend_page_load()

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('入口与展示')
    @allure.title('从通讯录成功进入好友资料页并校验-状态：已完成')
    def test_entry_and_profile_display(self):
        """从通讯录列表成功点击好友，进入资料页验证顶部大字昵称、ID及所在地信息完整展示"""
        with allure.step('1. 从通讯录中点击进入好友B的资料详情页'):
            success = self._go_to_contact_detail_from_list(RECEIVER_NAME)
            check.is_true(success, f'❌ 通讯录中未找到并点击好友: {RECEIVER_NAME}')
        with allure.step('2. 校验好友资料卡信息展示'):
            main_name = self.contactDetailPageS.get_formatted_friend_name()
            st_id = self.contactDetailPageS.get_st_id()
            location = self.contactDetailPageS.get_location()
            check.equal(main_name, RECEIVER_NAME, f'❌ 资料页主名称与预期不符，实际: {main_name}')
            check.is_true(len(st_id) > 0, '❌ 资料页显示的ID为空')
            check.is_true(len(location) > 0, '❌ 资料页显示的地区所在地为空')

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('设置备注名')
    @allure.title('修改备注名、各处同步并在清空后恢复-参数化边界字数限制校验-状态：已完成')
    @pytest.mark.parametrize('input_remark, expected_remark', [pytest.param('DYNAMIC_TIME', 'DYNAMIC_TIME', id='正常修改备注'), pytest.param('A' * 30, 'A' * 30, id='30个字符'), pytest.param('B' * 31, 'B' * 30, id='超过30个字符')])
    def test_modify_contact_remark_and_sync(self, input_remark, expected_remark):
        """修改备注名保存 -> 校验资料卡、通讯录同步显示 -> 清空备注名 -> 恢复原名称展示 (参数化合并)"""
        if input_remark == 'DYNAMIC_TIME':
            input_remark = expected_remark = f'测试备注_{int(time.time())}'
        with allure.step('1. 进入资料页并修改备注名'):
            self._go_to_remark_setting_page()
            self.remarkSettingPageS.click_remark_name()
            self.remarkSettingPageS.input_remark_name(input_remark)
            self.remarkSettingPageS.click_save()
            self.contactDetailPageS.click_iv_back()
            self.contactDetailPageS.wait_for_detail_page_load()
        with allure.step('2. 校验资料页大字正确展示新备注名，小字展示原昵称'):
            main_name = self.contactDetailPageS.get_formatted_friend_name()
            small_name = self.contactDetailPageS.get_contact_nickname(raise_exception=False)
            check.equal(main_name, expected_remark, f'❌ 资料卡顶部未成功显示修改后的备注名: {expected_remark}')
            check.is_in(RECEIVER_NAME, small_name, f'❌ 资料卡昵称小字处未成功保留显示好友原名称: {RECEIVER_NAME}')
        with allure.step('3. 校验通讯录好友列表中同步为新备注名'):
            self.contactDetailPageS.click_iv_back()
            self.homePageS.wait_for_friend_page_load()
            has_remark = self.contactSelectPageS.select_contact_by_name(expected_remark)
            check.is_true(bool(has_remark), f'❌ 备注修改后，通讯录中找不到带有新备注名的联系人: {expected_remark}')
        with allure.step('4. 清空备注名并保存，校验是否成功恢复为原名称显示'):
            self._go_to_remark_setting_page(name=expected_remark)
            self.remarkSettingPageS.click_remark_name()
            self.remarkSettingPageS.clear_remark_name()
            self.remarkSettingPageS.click_save()
            self.contactDetailPageS.click_iv_back()
            self.contactDetailPageS.wait_for_detail_page_load()
        with allure.step('5. 校验通讯录好友列表同步恢复'):
            after_main_name = self.contactDetailPageS.get_formatted_friend_name()
            after_small_name = self.contactDetailPageS.get_contact_nickname(raise_exception=False)
            check.equal(after_main_name, RECEIVER_NAME, f'❌ 资料卡顶部未成功恢复显示原昵称，实际显示：{after_main_name}')
            check.is_false(bool(after_small_name), f'❌ 清空备注后，资料卡仍显示昵称小字：{after_small_name}')
            self.contactDetailPageS.click_iv_back()
            self.homePageS.wait_for_friend_page_load()
            time.sleep(0.5)
            has_remark = self.contactSelectPageS.select_contact_by_name(RECEIVER_NAME)
            check.is_true(bool(has_remark), f'❌ 清空备注后通讯录未恢复展示好友原昵称')

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('电话管理')
    @allure.title('新增电话号码参数化校验（上限3个/数字限制/15字字符截断）-状态：已完成')
    @pytest.mark.parametrize('scenario, input_phones, expected_phones', [pytest.param('LIMIT_COUNT', ['13800000001', '13800000002', '13800000003', '13800000004'], ['13800000001', '13800000002', '13800000003'], id='限制输入最多3个'), pytest.param('ONLY_DIGITS', ['1380000abc'], ['1380000'], id='只允许输入数字'), pytest.param('MAX_LENGTH', ['1' * 16], ['1' * 15], id='最多输入15个字符')])
    def test_phone_number_addition_and_limit(self, scenario, input_phones, expected_phones):
        """新增电话号码参数化校验：测试只能添加3个、只允许数字、最多输入15个字"""
        with allure.step(f'1. 进入设置备注与电话页，尝试输入测试号码 - 场景: {scenario}'):
            self._go_to_phone_setting_page()
        with allure.step('2. 尝试添加电话号码并校验数量限制'):
            box_count = len(self.remarkSettingPageS.get_phones(False))
            if box_count >= 3:
                is_visible = self.remarkSettingPageS.is_add_phone_visible(False)
                check.is_false(is_visible, '❌ 已添加3个电话，但‘添加电话’按钮依然可见，未作数量上限控制')
            else:
                add_count = 3 - box_count
                for i, phone_val in enumerate(input_phones):
                    is_visible = self.remarkSettingPageS.is_add_phone_visible(False)
                    if i >= add_count and (not is_visible):
                        check.is_false(is_visible, '❌ 到达上限后，添加电话按钮隐藏异常 ')
                        break
                    if is_visible:
                        self.remarkSettingPageS.click_add_phone()
                    self.remarkSettingPageS.input_phone(phone_val, index=i, by_action=True)
        with allure.step('2. 前端即时校验：校验输入框中的文本变化是否符合规则'):
            current_phones = self.remarkSettingPageS.get_phones(False)
            if scenario == 'ONLY_DIGITS':
                check.equal(current_phones, expected_phones, f'❌ 前端未实时限制纯数字输入，当前输入框: {current_phones}')
            elif scenario == 'MAX_LENGTH':
                check.equal(current_phones, expected_phones, f'❌ 前端未实时限制15字上限截断，当前输入框: {current_phones}')
        with allure.step('3. 保存电话并重新进入，校验号码持久化回显是否符合预期'):
            self.remarkSettingPageS.click_save()
            self.remarkSettingPageS.wait_friend_detail_page()
        with allure.step('4. 校验已添加的电话号码回显'):
            ph_list = self.remarkSettingPageS.get_phone_numbers()
            check.is_true(all((p in expected_phones for p in ph_list)), f'❌ 已添加的电话号码回显不符合预期，实际: {ph_list}, 预期: {expected_phones}')
            self.contactDetailPageS.click_iv_back()
        with allure.step('5. 好友资料页面，校验号码回显'):
            if len(expected_phones) >= 3:
                self.contactDetailPageS.click_all_phone_numbers()
                self.contactDetailPageS.wait_for_phone_sheet_load()
                sheet_list = self.contactDetailPageS.get_sheet_phone_list()
                check.is_true(all((p in expected_phones for p in sheet_list)), f'❌ 已添加的电话号码回显不符合预期，实际: {sheet_list}, 预期: {expected_phones}')
                self.contactDetailPageS.click_phone_sheet_close()
            else:
                ph_list = self.contactDetailPageS.get_profile_phone_value()
                check.is_true(all((p in expected_phones for p in ph_list)), f'❌ 已添加的电话号码回显不符合预期，实际: {ph_list}, 预期: {expected_phones}')
        with allure.step('6. 重新进入设置备注与电话页，校验号码持久化回显'):
            self.contactDetailPageS.click_friend_detail_title_remark()
            self.remarkSettingPageS.wait_friend_detail_page()
            self.remarkSettingPageS.click_phone_item()
            actual_phones = self.remarkSettingPageS.get_phones(False)
            check.equal(actual_phones, expected_phones, f'❌ 保存后回显号码与预期不符，实际: {actual_phones}, 预期: {expected_phones}')
        with allure.step('7. 环境还原：清空本次输入的所有电话并保存'):
            self.remarkSettingPageS.delete_all_phones()
            self.remarkSettingPageS.click_save()
            aftph_list = self.remarkSettingPageS.get_phone_numbers()
            check.is_true(len(aftph_list) == 0, f'❌ 清空后回显号码与预期不符，实际: {aftph_list}, 预期: []')
            self.contactDetailPageS.click_iv_back()
            is_exist = self.contactDetailPageS.is_row_profile_phone()
            check.is_false(is_exist, f'❌ 清空后资料卡电话行不符合预期，实际: {is_exist}, 预期: False')

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('电话管理')
    @allure.title('删除电话号码及添加按钮重新显露逻辑-状态：已完成')
    def test_phone_number_deletion_flow(self):
        """测试删除其中一个电话，校验添加按钮重新显示流程"""
        with allure.step('1. 前置准备：进入备注页，添加2个电话并保存'):
            self._go_to_phone_setting_page()
            self.remarkSettingPageS.click_add_phone()
            self.remarkSettingPageS.input_phone('13900000001', index=0)
            self.remarkSettingPageS.click_add_phone()
            self.remarkSettingPageS.input_phone('13900000002', index=1)
            self.remarkSettingPageS.click_save()
            self.remarkSettingPageS.wait_friend_detail_page()
        with allure.step('2. 重新进入编辑页并删除第二个电话'):
            self.remarkSettingPageS.click_phone_item()
            self.remarkSettingPageS.clear_phone(index=1)
        with allure.step('3. 校验‘添加电话’按钮重新显露'):
            is_visible_after_del = self.remarkSettingPageS.is_add_phone_visible()
            check.is_true(is_visible_after_del, '❌ 删除1个电话后，‘添加电话’按钮未重新显露')
        with allure.step('4. 保存并重新进入，校验只剩下了第一个电话'):
            self.remarkSettingPageS.click_save()
            self.contactDetailPageS.click_iv_back()
            self.contactDetailPageS.wait_for_detail_page_load()
            ph_list = self.contactDetailPageS.get_profile_phone_value()
            check.is_true(len(ph_list) == 1, f'❌ 保存后重新进入，已保存的电话号码条数不等于1，实际为: {len(ph_list)}')
            if ph_list:
                check.equal(ph_list[0], '13900000001', f'❌ 剩余电话号码内容与预期不符，实际: {ph_list[0]}')
        with allure.step('5. 进入设置备注与电话页，校验只剩下了第一个电话'):
            self.contactDetailPageS.click_friend_detail_title_remark()
            self.remarkSettingPageS.wait_friend_detail_page()
            self.remarkSettingPageS.click_phone_item()
            phones = self.remarkSettingPageS.get_phones()
            check.equal(len(phones), 1, f'❌ 保存后重新进入，已保存的电话号码条数不等于1，实际为: {len(phones)}')
            if phones:
                check.equal(phones[0], '13900000001', f'❌ 剩余电话号码内容与预期不符，实际: {phones[0]}')
        with allure.step('6. Environment Teardown：全部清除后保存退出'):
            self.remarkSettingPageS.delete_all_phones()
            self.remarkSettingPageS.click_save()
            self.contactDetailPageS.click_iv_back()

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('标签')
    @allure.title('标签点击后选中/取消选中状态切换-状态：已完成')
    def test_tag_selection_and_toggle(self):
        """TextView 标签点击后应在选中（绿色）与未选中（灰色）状态间切换。"""
        with allure.step('1. 进入标签选择页并清理当前选中状态'):
            self._go_to_remark_setting_page()
        with allure.step('2. 清理当前已有标签选中状态'):
            tag_values = self.remarkSettingPageS.get_tag_values()
            self.remarkSettingPageS.click_tags()
            self.remarkSettingPageS.wait_for_tag_page_load()
            if tag_values:
                self.remarkSettingPageS.clear_tag(list_tags=tag_values)
                toast = self.remarkSettingPageS.get_toast()
                check.equal('保存成功', toast, f'❌ 未收到保存成功的 Toast，实际: {toast}')
        with allure.step('3. 获取当前标签名称并断言（若无可用标签则自动创建并取消默认勾选）'):
            tag_names = self.remarkSettingPageS.get_tag_names()
            if not tag_names:
                logger.info('ℹ️ 未发现可用标签，自动创建一个标签')
                new_tag = 'qa_auto_toggle'
                self.remarkSettingPageS.click_add_new_tag()
                self.remarkSettingPageS.input_tag_name(new_tag)
                self.remarkSettingPageS.click_create_done()
                self.remarkSettingPageS.wait_for_tag_page_load()
                self.remarkSettingPageS.click_tag(tag_type=1, target=new_tag)
                tag_names = self.remarkSettingPageS.get_tag_names()
            check.is_true(tag_names, '❌ 标签选择页没有找到 chip_group 下的 TextView 标签')
            if not tag_names:
                pytest.fail('标签选择页没有可操作的 TextView 标签')
            tag_name = tag_names[0]
        with allure.step(f'4. 点击标签 [{tag_name}]，校验变为选中状态（绿色）'):
            click_tag = self.remarkSettingPageS.click_tag(tag_type=1, target=tag_name)
            check.is_true(click_tag, f'❌ 点击标签 [{tag_name}] 失败')
            is_selected = self.remarkSettingPageS.is_tag_selected(tag_name)
            check.is_true(is_selected, f'❌ 点击标签 [{tag_name}] 后未变为选中状态')
        with allure.step(f'5. 再次点击标签 [{tag_name}]，校验取消选中（灰色）'):
            click_tag = self.remarkSettingPageS.click_tag(tag_type=1, target=tag_name)
            check.is_true(click_tag, f'❌ 再次点击标签 [{tag_name}] 失败')
            after_unselected = self.remarkSettingPageS.is_tag_selected(tag_name)
            check.is_false(after_unselected, f'❌ 再次点击后标签 [{tag_name}] 仍处于选中状态')
        with allure.step('6. 取消编辑并平滑退回好友详情页'):
            self.remarkSettingPageS.click_tv_cancel()
            self.contactDetailPageS.cancel_two_btn_comment()
            self.remarkSettingPageS.click_tv_cancel()
            self.remarkSettingPageS.wait_friend_detail_page()
            self.contactDetailPageS.click_iv_back()
            self.contactDetailPageS.wait_for_detail_page_load()

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('标签')
    @allure.title('选择标签及标签上限边界参数化校验-状态：已完成')
    @pytest.mark.parametrize('select_count, expected_selected_count, check_exceed_toast', [pytest.param(1, 1, False, id='选择1个标签'), pytest.param(14, 14, False, id='选择14个标签'), pytest.param(15, 15, False, id='选择15个标签'), pytest.param(16, 15, True, id='选择16个标签受阻')])
    def test_tag_selection_boundary_limit(self, select_count, expected_selected_count, check_exceed_toast):
        """通过参数化模式合并校验标签的最大选择上限及超限拦截逻辑"""
        with allure.step('1. 进入标签选择页并清理当前已有选中状态'):
            self._prepare_tag_page_and_clean()
        tag_names = self.remarkSettingPageS.get_tag_names(timeout=10)
        required_tags = max(select_count, 15)
        if len(tag_names) < required_tags:
            missing_count = required_tags - len(tag_names)
            logger.info(f'ℹ️ 当前标签数量为 {len(tag_names)}，不足所需 {required_tags} 个。自动新建 {missing_count} 个测试标签...')
            for idx in range(missing_count):
                new_tag = f'qa{int(time.time())}_{idx:02d}'
                self.remarkSettingPageS.click_add_new_tag()
                self.remarkSettingPageS.input_tag_name(new_tag)
                self.remarkSettingPageS.click_create_done()
                self.remarkSettingPageS.wait_for_tag_page_load()
                self.remarkSettingPageS.click_tag(tag_type=1, target=new_tag)
            tag_names = self.remarkSettingPageS.get_tag_names(timeout=10)
        click_count = min(select_count, 15)
        with allure.step(f'2. 依次选择前 {click_count} 个标签'):
            self.remarkSettingPageS.click_tag(tag_type=0, target=click_count)
        if check_exceed_toast:
            with allure.step('3. 尝试点击第 16 个标签，校验被拦截并弹出 Toast'):
                sixteenth_tag_name = tag_names[15]
                self.remarkSettingPageS.click_tag(tag_type=1, target=sixteenth_tag_name)
                sel_toast = self.remarkSettingPageS.get_toast(timeout=10)
                is_selected = self.remarkSettingPageS.is_tag_selected(sixteenth_tag_name)
                check.is_false(is_selected, f'❌ 第16个标签 [{sixteenth_tag_name}] 不应被选中')
                check.is_in('最多选择15个标签', sel_toast, f'❌ 未收到15个标签上限 Toast，实际: {sel_toast}')
        with allure.step(f'4. 校验最终资料页和卡片页选中的标签数量为 {expected_selected_count}'):
            self.remarkSettingPageS.click_save()
            self.remarkSettingPageS.wait_friend_detail_page(timeout=15)
            selected_tags = self.remarkSettingPageS.get_tag_page_values(tag_type=0, split_type=0)
            check.equal(len(selected_tags), expected_selected_count, f'❌ 备注设置页标签选中数量不等于 {expected_selected_count}')
            self.contactDetailPageS.click_iv_back()
            self.contactDetailPageS.wait_for_detail_page_load()
            out_tags = self.remarkSettingPageS.get_tag_page_values(tag_type=1, split_type=1)
            check.equal(len(out_tags), expected_selected_count, f'❌ 资料卡展示标签数量不等于 {expected_selected_count}')
        with allure.step('5. 环境恢复：进入设置页清空所有选中标签'):
            self._clean_tags_and_back_to_detail()

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('标签')
    @allure.title('新增标签30字限制及新增后默认选中-状态：已完成')
    @pytest.mark.destructive
    @pytest.mark.parametrize('input_length, expected_length', [pytest.param(29, 29, id='29字-上限前'), pytest.param(30, 30, id='30字-正好上限'), pytest.param(31, 30, id='31字-超限截断')])
    def test_create_tag_length_and_auto_selected(self, input_length: int, expected_length: int):
        """参数化校验标签名称长度边界，且新增成功后默认处于选中状态。"""
        with allure.step('1. 进入标签选择页并清理已有标签'):
            self._prepare_tag_page_and_clean()
        unique_prefix = f'qa{time.time_ns()}_{input_length}'
        tag_name = (unique_prefix + 'x' * input_length)[:input_length]
        expected_tag_name = tag_name[:expected_length]
        with allure.step(f'2. 新增{input_length}字标签，校验实际保留{expected_length}字'):
            self.remarkSettingPageS.click_add_new_tag()
            self.remarkSettingPageS.input_tag_name(tag_name)
            self.remarkSettingPageS.click_create_done()
            self.remarkSettingPageS.wait_for_tag_page_load()
            self.remarkSettingPageS.input_search_tag(expected_tag_name)
            tag_names = self.remarkSettingPageS.get_tag_names(timeout=5)
            check.equal(len(tag_names[-1]), expected_length, f'❌ 输入{input_length}字时长度处理错误，预期保留{expected_length}字，实际保留{len(tag_names[-1])}字')
            check.equal(tag_names[-1], expected_tag_name, f'❌ 标签输入框最终内容不符合预期，实际: {tag_names[-1]}')
        with allure.step('3. 校验新增后的标签名称及默认选中状态'):
            check.is_in(expected_tag_name, tag_names, f'❌ 新增标签未出现在标签列表: {expected_tag_name}')
            if expected_tag_name in tag_names:
                check.is_true(self.remarkSettingPageS.is_tag_selected(expected_tag_name), f'❌ 新增标签 [{expected_tag_name}] 未默认选中')
        with allure.step('4. 环境恢复：清空创建的测试标签'):
            self._cancel_from_tag_search_to_detail()

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('标签')
    @allure.title('新增标签数量边界及保存回显参数化校验-状态：已完成')
    @pytest.mark.destructive
    @pytest.mark.parametrize('create_count, expected_count, check_exceed_toast, should_save, is_first', [pytest.param(1, 1, False, True, True, id='新增1个标签并保存回显'), pytest.param(14, 14, False, False, False, id='新增14个标签'), pytest.param(15, 15, False, False, False, id='新增15个标签上限'), pytest.param(16, 16, True, False, False, id='新增16个标签受阻')])
    def test_create_tag_max_count_limit_toast(self, create_count: int, expected_count: int, check_exceed_toast: bool, should_save: bool, is_first: bool):
        """校验新增不同数量标签边界、上限 Toast 拦截以及正向保存回显闭环 (参数化合并)。"""
        with allure.step('0. 状态自愈：确保停留在好友列表页面（HomePage）'):
            if is_first:
                if not self.homePageS.wait_for_friend_page_load(timeout=1):
                    if self.contactDetailPageS.wait_for_detail_page_load(timeout=1, raise_exception=False):
                        self.contactDetailPageS.click_iv_back()
                        self.homePageS.wait_for_friend_page_load(timeout=2)
                    else:
                        logger.info('当前页面既非详情页也非好友列表页，尝试执行深度自愈退回...')
                        self.mainPageS.go_to_main_page()
                        self.homePageS.click_bottom_expand_button()
                        self.homePageS.click_friend()
                        self.homePageS.wait_for_friend_page_load()
                self._clear_all_tags()
            self._prepare_tag_page_and_clean()
        test_prefix = f'qa{int(time.time())}'
        actual_add_count = min(create_count, 15)
        with allure.step(f'2. 尝试连续新增 {actual_add_count} 个标签'):
            for index in range(actual_add_count):
                tag_name = f'{test_prefix}_{index:02d}'
                self.remarkSettingPageS.click_add_new_tag()
                self.remarkSettingPageS.input_tag_name(tag_name)
                self.remarkSettingPageS.click_create_done()
                self.remarkSettingPageS.wait_for_tag_page_load()
        if check_exceed_toast:
            with allure.step(f'3. 尝试新增第 {create_count} 个标签，校验被限制并弹出 Toast'):
                sixteenth_name = f'{test_prefix}_15'.ljust(30, 'x')
                self.remarkSettingPageS.click_add_new_tag()
                self.remarkSettingPageS.input_tag_name(sixteenth_name)
                self.remarkSettingPageS.click_create_done()
                toast_exceed = self.remarkSettingPageS.get_toast('最多选择15个标签', timeout=2)
                check.is_true(toast_exceed, f'❌ 未收到最多选择15个标签的 Toast 拦截提示')
        if should_save:
            with allure.step('4. 点击保存并验证资料卡成功同步渲染新标签'):
                self.remarkSettingPageS.click_save()
                self.remarkSettingPageS.wait_friend_detail_page()
                self.contactDetailPageS.click_iv_back()
                out_tags = self.remarkSettingPageS.get_tag_page_values(tag_type=1, split_type=1)
                check.is_true(any((test_prefix in tag for tag in out_tags)), f'❌ 资料卡未同步展示新保存的标签: {out_tags}')
        else:
            self._cancel_from_tag_search_to_detail()
        with allure.step('5. 环境恢复：安全清空标签并退回好友详情页'):
            self.contactDetailPageS.click_iv_back()
            self.homePageS.wait_for_friend_page_load()
            self._clear_all_tags()

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('备忘描述')
    @allure.title('备忘描述多行Emoji及上限(200字)边界参数化校验-状态：已完成')
    @pytest.mark.parametrize('input_note, expected_note', [pytest.param('第一行：测试账号特性描述\n第二行：具有高可靠性校验🌟', '第一行：测试账号特性描述\n第二行：具有高可靠性校验🌟', id='多行带Emoji描述'), pytest.param('q' * 199, 'q' * 199, id='199字-上限前'), pytest.param('q' * 200, 'q' * 200, id='200字-正好上限'), pytest.param('q' * 201, 'q' * 200, id='201字-超限截断')])
    def test_multi_line_description_note(self, input_note: str, expected_note: str):
        """修改备忘描述保存 -> 校验资料卡与设置页双重回显及200字上限 -> 清理备忘描述 -> 安全恢复导航 (参数化合并)"""
        with allure.step(f'1. 进入设置备注页，点击备忘入口，输入描述文本(长度:{len(input_note)})并保存'):
            self._go_to_remark_setting_page()
            self.remarkSettingPageS.click_memo()
            self.remarkSettingPageS.input_note(input_note)
            self.remarkSettingPageS.click_save()
            self.remarkSettingPageS.wait_friend_detail_page(timeout=20)
            self.contactDetailPageS.click_iv_back()
            self.contactDetailPageS.wait_for_detail_page_load()
        with allure.step(f'2. 在好友资料卡页面，校验备忘描述显示内容与实际保存长度'):
            profile_note = self.remarkSettingPageS.get_profile_memo_value()
            check.equal(len(profile_note), len(expected_note), f'❌ 资料卡备忘实际显示长度 ({len(profile_note)}) 与预期 ({len(expected_note)}) 不符')
            check.equal(profile_note, expected_note, f'❌ 资料卡备忘内容回显不匹配，实际: {profile_note}')
        with allure.step(f'3. 重新进入设置备注页，校验编辑框/页面内部备忘回显'):
            self.contactDetailPageS.click_friend_detail_title_remark()
            self.remarkSettingPageS.wait_friend_detail_page()
            displayed_note = self.remarkSettingPageS.get_note()
            check.equal(len(displayed_note), len(expected_note), f'❌ 设置页备忘实际保存长度 ({len(displayed_note)}) 与预期上限 ({len(expected_note)}) 不符')
            check.equal(displayed_note, expected_note, f'❌ 设置页备忘内容回显不匹配，实际: {displayed_note}')
        with allure.step('4. 环境恢复：清空备忘描述并安全退回好友详情页'):
            self.remarkSettingPageS.click_memo()
            self.remarkSettingPageS.clear_note()
            self.remarkSettingPageS.click_save()
            self.remarkSettingPageS.wait_friend_detail_page(timeout=20)
            self.contactDetailPageS.click_iv_back()
            self.contactDetailPageS.wait_for_detail_page_load()

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('共同群聊')
    @allure.title('共同群聊入口展示、点击列表项跳转至群聊窗口校验-状态：已完成')
    def test_common_groups_navigation_and_search(self):
        """校验存在共同群聊时资料页的展示，进入共同群聊列表后点击具体群聊切入聊天界面并比对群名"""
        with allure.step('1. 进入好友资料卡并点进设置备注页，验证共同群聊展示个数'):
            self._go_to_remark_setting_page()
            count = self.remarkSettingPageS.get_common_groups_count()
            if count == 0:
                pytest.skip('当前测试账号与好友无共同群聊，跳过本用例')
        with allure.step('2. 点击【我和他(她)的共同群聊】，进入共同群聊详情页面'):
            self.remarkSettingPageS.click_common_groups()
            is_loaded = self.remarkSettingPageS.wait_for_common_groups_page_load()
            check.is_true(is_loaded, '❌ 共同群聊详情页未在预期时间内加载完成')
        with allure.step('3. 获取共同群聊列表，并选中第一个群聊名称'):
            group_names = self.remarkSettingPageS.get_common_group_names()
            check.greater(len(group_names), 0, '❌ 共同群聊列表未加载到任何群聊项目')
        with allure.step(f"4. 点击共同群聊条目 '{group_names[0]}'，跳转至群聊窗口"):
            click_res = self.remarkSettingPageS.click_common_group_by_name(group_names[0])
            check.is_true(click_res, f"❌ 点击共同群聊 '{group_names[0]}' 失败")
        with allure.step('5. 校验群聊窗口顶部名称与选中的共同群聊名称一致'):
            actual_group_name = self.chatPageS.get_group_name()
            check.equal(actual_group_name, group_names[0], f"❌ 聊天窗口顶部群名 '{actual_group_name}' 与期待的共同群名 '{group_names[0]}' 不相符")
        with allure.step('6. 逐级退回：聊天窗口 → 共同群聊列表 → 设置备注页 → 好友资料页'):
            self.chatPageS.click_back_button()
            self.remarkSettingPageS.wait_for_common_groups_page_load()
            self.contactDetailPageS.click_iv_back()
            self.remarkSettingPageS.wait_friend_detail_page()
            self.contactDetailPageS.click_iv_back()
