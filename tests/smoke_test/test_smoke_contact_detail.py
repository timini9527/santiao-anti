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

class BaseSmokeContactDetail:
    """好友资料与备注设置测试基类，统一管理 Page 实例化与后置清理"""

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender):
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        self.contactDetailPage = ContactDetailPage(driver_sender)
        self.remarkSettingPage = RemarkSettingPage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.tagGroupPage = ContactTagGroupPage(driver_sender)
        yield
        try:
            self.mainPage.go_to_main_page()
        except Exception:
            pass



@allure.epic('IM核心功能测试')
@allure.feature('冒烟测试-好友资料与备注设置')
class TestSmokeContactDetail(BaseSmokeContactDetail):
    """好友资料卡详情管理与备注设置冒烟测试集 (覆盖核心主路径)"""

    def _enter_friend_list_page(self):
        """通用入口导航：进入好友列表主页面"""
        self.mainPage.go_to_main_page()
        self.homePage.click_bottom_expand_button()
        self.homePage.click_friend()
        self.homePage.wait_for_friend_page_load()

    def _click_contact_by_name(self, name: str, raise_exception: bool=True, search: bool=False) -> bool:
        """在好友列表点击指定联系人并等待详情页加载"""
        click_ok = self.contactSelectPage.click_contact_by_name(name, raise_exception=raise_exception, search=search)
        if click_ok:
            self.contactDetailPage.wait_for_detail_page_load(timeout=8)
        return click_ok

    def _go_to_contact_detail_from_list(self, name: str, raise_exception: bool=False) -> bool:
        """导航至指定好友的资料详情页"""
        self._enter_friend_list_page()
        return self._click_contact_by_name(name, raise_exception=raise_exception)

    def _go_to_remark_setting_page(self, name: str=RECEIVER_NAME):
        """进入指定好友的设置备注页"""
        self._go_to_contact_detail_from_list(name)
        self.contactDetailPage.click_friend_detail_title_remark()
        self.remarkSettingPage.wait_friend_detail_page()

    def _prepare_tag_page_and_clean(self):
        """进入标签选择页并清理当前已选中的标签，确保最终稳定停留在标签选择页"""
        self._go_to_remark_setting_page()
        tag_values = self.remarkSettingPage.get_tag_values()
        self.remarkSettingPage.click_tags()
        self.remarkSettingPage.wait_for_tag_page_load()
        if tag_values:
            self.remarkSettingPage.clear_tag(list_tags=tag_values)
            self.remarkSettingPage.wait_friend_detail_page()
            self.remarkSettingPage.click_tags()
            self.remarkSettingPage.wait_for_tag_page_load()

    def _clean_tags_and_back_to_detail(self):
        """在标签页/备注页清理已选标签并安全切回好友详情页 (自愈兼容)"""
        if self.remarkSettingPage.wait_for_tag_page_load(timeout=1):
            self.contactDetailPage.click_iv_back()
            self.remarkSettingPage.wait_friend_detail_page(timeout=2)
        if self.contactDetailPage.wait_for_detail_page_load(timeout=1, raise_exception=False):
            self.contactDetailPage.click_friend_detail_title_remark()
            self.remarkSettingPage.wait_friend_detail_page(timeout=3)
        tag_values = self.remarkSettingPage.get_tag_values()
        if tag_values:
            self.remarkSettingPage.click_tags()
            self.remarkSettingPage.wait_for_tag_page_load()
            self.remarkSettingPage.clear_tag(list_tags=tag_values)
            self.remarkSettingPage.wait_friend_detail_page()
        self.contactDetailPage.click_iv_back()
        self.contactDetailPage.wait_for_detail_page_load(timeout=3)

    def _go_to_phone_setting_page(self):
        """进入好友电话列表项"""
        self._go_to_remark_setting_page()
        self.remarkSettingPage.click_phone_item()

    def _clear_specific_tag(self, tag_name: str):
        """精准删除指定名称的分组标签，保护环境隔离性不影响其他分组"""
        logger.info(f"⚙️ [SmokeClean] 精准清理测试生成的临时标签分组: {tag_name}")
        self.homePage.click_category_manager()
        self.tagGroupPage.wait_for_group_list_page_load(page_title='0')
        self.tagGroupPage.delete_group_or_all_groups_flow(group_name=tag_name, is_all=False)
        self.contactDetailPage.click_iv_back()
        self.homePage.wait_for_friend_page_load()

    def _clear_all_tags(self):
        """进入好友页面-分组管理-删除所有分组 (保留兼容全量清理)"""
        with allure.step('1. 进入分组管理页面'):
            self.homePage.click_category_manager()
            self.tagGroupPage.wait_for_group_list_page_load(page_title='0')
            group_names = self.tagGroupPage.get_group_tag_names(timeout=1, raise_exception=False)
            if not group_names:
                logger.info('✅ [Action - TagGroup] 分组管理页面分组已全部删除，无需再操作')
                self.contactDetailPage.click_iv_back()
                return
        with allure.step('2. 执行批量清空所有分组操作'):
            del_all_result = self.tagGroupPage.delete_group_or_all_groups_flow(is_all=True)
            check.is_true(del_all_result, '❌ 批量清空所有分组流执行失败')
        with allure.step('3. 校验列表是否已完全清空'):
            self.tagGroupPage.wait_for_group_list_page_load(page_title='0')
            remaining_names = self.tagGroupPage.get_group_tag_names(timeout=1, raise_exception=False)
            check.equal(len(remaining_names), 0, f'❌ 批量删除后列表中依然残留分组: {remaining_names}')
        with allure.step('4. 返回好友列表主页面'):
            self.contactDetailPage.click_iv_back()
            self.homePage.wait_for_friend_page_load()

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @allure.story('入口与展示')
    @allure.title('从通讯录成功进入好友资料页并校验信息-状态：已完成')
    def test_smoke_entry_and_profile_display(self):
        """从通讯录列表进入好友资料详情页，验证昵称、ID及所在地信息完整展示"""
        with allure.step('1. 从通讯录中点击进入好友的资料详情页'):
            success = self._go_to_contact_detail_from_list(RECEIVER_NAME)
            check.is_true(success, f'❌ 通讯录中未找到并点击好友: {RECEIVER_NAME}')
        with allure.step('2. 校验好友资料卡信息展示'):
            main_name = self.contactDetailPage.get_formatted_friend_name()
            st_id = self.contactDetailPage.get_st_id()
            location = self.contactDetailPage.get_location()
            check.equal(main_name, RECEIVER_NAME, f'❌ 资料页主名称与预期不符，实际: {main_name}')
            check.is_true(len(st_id) > 0, '❌ 资料页显示的ID为空')
            check.is_true(len(location) > 0, '❌ 资料页显示的地区所在地为空')

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @allure.story('设置备注名')
    @allure.title('正常修改备注名并同步，校验后恢复-状态：已完成')
    def test_smoke_modify_contact_remark_and_sync(self):
        """修改备注名 -> 校验资料卡(大字备注+小字原昵称)、通讯录同步 -> 清空备注名并恢复"""
        input_remark = f'A测试备注_{int(time.time())}'

        try:
            with allure.step('1. 进入资料页并修改备注名'):
                self._go_to_remark_setting_page(RECEIVER_NAME)
                self.remarkSettingPage.click_remark_name()
                self.remarkSettingPage.input_remark_name(input_remark)
                self.remarkSettingPage.click_save()
                self.contactDetailPage.click_iv_back()
                self.contactDetailPage.wait_for_detail_page_load()

            with allure.step('2. 校验资料卡大字展示新备注名，小字保留展示原昵称'):
                main_name = self.contactDetailPage.get_formatted_friend_name()
                check.equal(main_name, input_remark, f'❌ 资料卡顶部未成功显示修改后的备注名: {input_remark}')
                small_name = self.contactDetailPage.get_contact_nickname(raise_exception=False)
                check.is_in(RECEIVER_NAME, small_name, f'❌ 资料卡昵称小字处未成功保留显示好友原名称: {RECEIVER_NAME}')

            with allure.step('3. 校验通讯录好友列表中同步为新备注名'):
                self.contactDetailPage.click_iv_back()
                self.homePage.wait_for_friend_page_load()
                has_remark = self.contactSelectPage.click_contact_by_name(input_remark, search=True)
                check.is_true(bool(has_remark), f'❌ 备注修改后，通讯录中找不到带有新备注名的联系人: {input_remark}')

        finally:
            with allure.step('4. 环境清理与恢复：清空备注名并保存，校验恢复为原昵称'):
                if not self.contactDetailPage.wait_for_detail_page_load(timeout=2, raise_exception=False):
                    self._go_to_contact_detail_from_list(input_remark)
                self.contactDetailPage.click_friend_detail_title_remark()
                self.remarkSettingPage.wait_friend_detail_page()
                self.remarkSettingPage.click_remark_name()
                self.remarkSettingPage.clear_remark_name()
                self.remarkSettingPage.click_save()
                self.contactDetailPage.click_iv_back()
                self.contactDetailPage.wait_for_detail_page_load()

            with allure.step('5. 校验资料卡与通讯录同步恢复原昵称展示'):
                after_main_name = self.contactDetailPage.get_formatted_friend_name()
                check.equal(after_main_name, RECEIVER_NAME, f'❌ 资料卡顶部未成功恢复显示原昵称，实际显示：{after_main_name}')
                after_small_name = self.contactDetailPage.get_contact_nickname(raise_exception=False)
                check.is_false(bool(after_small_name), f'❌ 清空备注后，资料卡仍残留显示昵称小字：{after_small_name}')
                self.contactDetailPage.click_iv_back()
                self.homePage.wait_for_friend_page_load()
                has_orig = self.contactSelectPage.click_contact_by_name(RECEIVER_NAME, search=True)
                check.is_true(bool(has_orig), f'❌ 清空备注后通讯录未恢复展示好友原昵称: {RECEIVER_NAME}')

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.smoke
    @allure.story('电话管理')
    @allure.title('新增电话号码回显校验并清空还原-状态：已完成')
    def test_smoke_phone_number_addition_and_deletion(self):
        """新增电话号码 -> 资料卡与设置页双重回显校验 -> 删除电话号码还原环境 (高健壮自愈)"""
        phone_val = f'138{int(time.time()) % 100000000:08d}'

        try:
            with allure.step('1. 进入设置备注与电话页，预检清理并输入测试号码'):
                self._go_to_phone_setting_page()
                current_existing = self.remarkSettingPage.get_phones(raise_exception=False)
                if current_existing:
                    self.remarkSettingPage.delete_all_phones()
                self.remarkSettingPage.click_add_phone()
                self.remarkSettingPage.input_phone(phone_val, index=0, by_action=True)

            with allure.step('2. 保存电话，校验设置备注页持久化正确回显'):
                self.remarkSettingPage.click_save()
                self.remarkSettingPage.wait_friend_detail_page()
                ph_list = self.remarkSettingPage.get_phone_numbers()
                check.is_in(phone_val, ph_list, f'❌ 设置备注页未成功回显电话号码: {phone_val}')
                self.contactDetailPage.click_iv_back()
                self.contactDetailPage.wait_for_detail_page_load()

            with allure.step('3. 返回好友资料卡页面，校验电话行正确回显'):
                profile_phones = self.contactDetailPage.get_profile_phone_value()
                check.is_in(phone_val, profile_phones, f'❌ 资料卡电话行未回显电话号码: {phone_val}')

        finally:
            with allure.step('4. 环境清理与恢复：清空删除所有电话并保存还原'):
                if self.contactDetailPage.wait_for_detail_page_load(timeout=2, raise_exception=False):
                    self.contactDetailPage.click_friend_detail_title_remark()
                    self.remarkSettingPage.wait_friend_detail_page()
                    self.remarkSettingPage.click_phone_item()
                self.remarkSettingPage.delete_all_phones()
                self.remarkSettingPage.click_save()
                self.remarkSettingPage.wait_friend_detail_page()
                self.contactDetailPage.click_iv_back()
                self.contactDetailPage.wait_for_detail_page_load()

            with allure.step('5. 校验资料卡电话行彻底清除'):
                is_exist = self.contactDetailPage.is_row_profile_phone()
                check.is_false(is_exist, '❌ 电话清空后，好友资料详情页依然残留显示了电话栏目')

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @allure.story('标签')
    @allure.title('选择标签并保存同步，校验后环境恢复-状态：已完成')
    def test_smoke_tag_selection_and_sync(self):
        """选择标签并保存 -> 校验卡片回显 -> 后置清理还原 (高健壮自愈与精准隔离)"""
        target_tag = ""
        is_new_tag = False

        try:
            with allure.step('1. 进入标签选择页并清理已选标签'):
                self._prepare_tag_page_and_clean()

            with allure.step('2. 获取现有标签（若无则新建一个）并进行选择'):
                tag_names = self.remarkSettingPage.get_tag_names()
                need_click = True
                if not tag_names:
                    target_tag = f'qa_smoke_{int(time.time())}'
                    is_new_tag = True
                    self.remarkSettingPage.click_add_new_tag()
                    self.remarkSettingPage.input_tag_name(target_tag)
                    self.remarkSettingPage.click_create_done()
                    self.remarkSettingPage.wait_for_tag_page_load()
                    need_click = False
                else:
                    target_tag = tag_names[0]

                if need_click:
                    self.remarkSettingPage.click_tag(tag_type=1, target=target_tag)

            with allure.step('3. 保存并验证设置页和资料卡页面成功回显选中标签'):
                self.remarkSettingPage.click_save()
                self.remarkSettingPage.wait_friend_detail_page()
                selected_tags = self.remarkSettingPage.get_tag_page_values(tag_type=0, split_type=0)
                check.is_in(target_tag, selected_tags, f'❌ 设置备注页未展示选中标签: {target_tag}')
                self.contactDetailPage.click_iv_back()
                self.contactDetailPage.wait_for_detail_page_load()
                out_tags = self.remarkSettingPage.get_tag_page_values(tag_type=1, split_type=1)
                check.is_in(target_tag, out_tags, f'❌ 资料详情卡未展示选中标签: {target_tag}')

        finally:
            with allure.step('4. 环境恢复：清除选中的标签并安全退回详情页'):
                self._clean_tags_and_back_to_detail()

            with allure.step('5. 校验资料卡标签彻底清除'):
                cleared_profile_tags = self.remarkSettingPage.get_tag_page_values(tag_type=1, split_type=1)
                check.is_not_in(target_tag, cleared_profile_tags, f'❌ 标签解绑后，资料详情卡依然残留展示该标签: {target_tag}')

            if is_new_tag and target_tag:
                with allure.step(f'6. 精准清理本次测试新建的标签分组: {target_tag}'):
                    self.contactDetailPage.click_iv_back()
                    self.homePage.wait_for_friend_page_load()
                    self._clear_specific_tag(target_tag)

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.smoke
    @allure.story('备忘描述')
    @allure.title('新增备忘描述回显校验与清除还原-状态：已完成')
    def test_smoke_memo_description(self):
        """输入备忘描述保存 -> 双重回显校验 -> 清除还原环境 (高健壮自愈与反向断言)"""
        note_val = f'冒烟测试_备忘_{int(time.time())}'

        try:
            with allure.step('1. 进入设置备注页，输入动态备忘描述并保存'):
                self._go_to_remark_setting_page()
                self.remarkSettingPage.click_memo()
                self.remarkSettingPage.input_note(note_val)
                self.remarkSettingPage.click_save()
                self.remarkSettingPage.wait_friend_detail_page()
                self.contactDetailPage.click_iv_back()
                self.contactDetailPage.wait_for_detail_page_load()

            with allure.step('2. 在好友资料卡页面校验备忘回显'):
                profile_note = self.remarkSettingPage.get_profile_memo_value()
                check.equal(profile_note, note_val, f'❌ 资料卡展示的备忘文本不符合预期，实际: {profile_note}')

            with allure.step('3. 重新进入设置备注页，校验编辑内备忘回显'):
                self.contactDetailPage.click_friend_detail_title_remark()
                self.remarkSettingPage.wait_friend_detail_page()
                displayed_note = self.remarkSettingPage.get_note()
                check.equal(displayed_note, note_val, f'❌ 备注页展示的备忘文本不符合预期，实际: {displayed_note}')

        finally:
            with allure.step('4. 环境恢复：清空备忘描述并安全退回详情页'):
                if self.contactDetailPage.wait_for_detail_page_load(timeout=2, raise_exception=False):
                    self.contactDetailPage.click_friend_detail_title_remark()
                    self.remarkSettingPage.wait_friend_detail_page()
                self.remarkSettingPage.click_memo()
                self.remarkSettingPage.clear_note()
                self.remarkSettingPage.click_save()
                self.remarkSettingPage.wait_friend_detail_page()
                self.contactDetailPage.click_iv_back()
                self.contactDetailPage.wait_for_detail_page_load()

            with allure.step('5. 校验资料卡备忘描述彻底清除'):
                cleared_memo = self.remarkSettingPage.get_profile_memo_value(raise_exception=False)
                check.is_false(bool(cleared_memo), f'❌ 备忘清空后，好友资料详情页依然残留展示了备忘描述: {cleared_memo}')

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.smoke
    @allure.story('共同群聊')
    @allure.title('进入共同群聊列表并点击切入聊天界面-状态：已完成')
    def test_smoke_common_groups_navigation(self):
        """共同群聊入口展示校验 -> 点击列表进入共同群聊 -> 切入聊天界面 -> 逐级回退"""
        with allure.step('1. 进入备注页，校验并获取共同群聊数量'):
            self._go_to_remark_setting_page()
            count = self.remarkSettingPage.get_common_groups_count()
            if count == 0:
                pytest.skip('当前账号无共同群聊，跳过共同群聊冒烟测试')
        with allure.step('2. 点击【共同群聊】入口，进入群聊详情页'):
            self.remarkSettingPage.click_common_groups()
            is_loaded = self.remarkSettingPage.wait_for_common_groups_page_load()
            check.is_true(is_loaded, '❌ 共同群聊详情页加载超时')
        with allure.step('3. 点击第一个共同群聊，进入聊天窗口'):
            group_names = self.remarkSettingPage.get_common_group_names()
            check.greater(len(group_names), 0, '❌ 共同群聊列表未获取到群聊项目')
            target_group = group_names[0]
            click_res = self.remarkSettingPage.click_common_group_by_name(target_group)
            check.is_true(click_res, f"❌ 点击共同群聊 '{target_group}' 失败")
        with allure.step('4. 校验聊天窗口顶部群名，并逐级安全退回'):
            actual_group_name = self.chatPage.get_group_name()
            check.equal(actual_group_name, target_group, f"❌ 聊天页面顶部展示的群名 '{actual_group_name}' 与预期不符")
            self.chatPage.click_back_button()
            self.remarkSettingPage.wait_for_common_groups_page_load()
            self.contactDetailPage.click_iv_back()
            self.remarkSettingPage.wait_friend_detail_page()
            self.contactDetailPage.click_iv_back()
            self.contactDetailPage.wait_for_detail_page_load(timeout=3, raise_exception=False)