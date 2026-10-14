import time
import allure
import pytest
from pytest_check import check
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.friend.tag_group.contact_tag_group_page import ContactTagGroupPage
from pages.common.contact_select_page import ContactSelectPage
from pages.friend.profile.contact_detail_page import ContactDetailPage
from core.logger_utils import logger





@allure.epic('通讯录模块')
@allure.feature('好友分组与标签管理')
class TestContactTagGroup:
    """微信好友分组/标签功能自动化测试集"""

    @pytest.fixture(scope='class', autouse=True)
    def setup_class_nav(self, driver_sender):
        """类级别前置：全类仅执行1次，从主页展开底栏并进入好友/通讯录列表页"""
        main_page = MainPage(driver_sender)
        home_page = HomePage(driver_sender)
        main_page.go_to_main_page()
        home_page.click_bottom_expand_button()
        home_page.click_friend()
        home_page.wait_for_friend_page_load()
        home_page.click_category_manager()

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender):
        """用例级别前置与后置：初始化页面对象，后置确保安全留在分组管理列表页"""
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        self.contactDetailPage = ContactDetailPage(driver_sender)
        self.tagGroupPage = ContactTagGroupPage(driver_sender)
        yield
        try:
            if not self.tagGroupPage.wait_for_group_list_page_load(timeout=2, raise_exception=False):
                self.tagGroupPage.click_iv_back()
                if not self.tagGroupPage.wait_for_group_list_page_load(timeout=2, raise_exception=False):
                    self.mainPage.go_to_main_page(raise_exception=False)
                    self.homePage.click_bottom_expand_button()
                    self.homePage.click_friend()
                    self.homePage.click_category_manager()
        except Exception as e:
            logger.error(f'⚠️ [Teardown] 返回分组列表页面失败: {e}')



    # =========================================================================
    # 辅助方法 (Helpers) - 提炼高频重复交互逻辑
    # =========================================================================
    def _create_subgroup_and_save(self, name: str, wait_toast: bool = True) -> bool:
        """辅助方法：新建分组并保存"""
        self.tagGroupPage.wait_for_group_list_page_load()
        self.tagGroupPage.click_add_subgroup()
        self.tagGroupPage.input_subgroup_name(name)
        self.tagGroupPage.click_save_group()
        if wait_toast:
            return bool(self.tagGroupPage.get_toast('保存成功', timeout=2))
        return True

    def _is_group_in_list(self, name: str) -> bool:
        """辅助方法：判断列表中是否存在指定分组（支持带有人数后缀的包含匹配）"""
        self.tagGroupPage.wait_for_group_list_page_load(raise_exception=False)
        group_names = self.tagGroupPage.get_group_tag_names(timeout=1, raise_exception=False)
        return any(name in g for g in group_names)

    def _cleanup_group(self, name: str):
        """辅助方法：环境清理，安全退回列表并删除指定分组"""
        if not self.tagGroupPage.wait_for_group_list_page_load(timeout=1, raise_exception=False):
            self.tagGroupPage.click_iv_back()
            self.tagGroupPage.click_cancel_dialog()
        if self._is_group_in_list(name):
            self.tagGroupPage.delete_group_or_all_groups_flow(group_name=name)


    # =========================================================================
    # 测试用例 (Testcases)
    # =========================================================================
    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story('新建与删除分组')
    @allure.title('FD_GROUP_TAG_001 - 正向创建好友分组、校验展示并成功删除闭环-状态：已完成')
    def test_create_and_delete_contact_group_normal(self):
        """测试创建新好友分组，校验保存后正确在分组列表显示，并测试删除销毁全流程"""
        test_group_name = f'自动化组_{int(time.time())}'
        try:
            with allure.step(f"1. 进入新建分组页，输入分组名称 '{test_group_name}' 并保存"):
                toast = self._create_subgroup_and_save(test_group_name)
                check.is_true(toast, '❌ 未收到分组创建成功的 Toast 提示')
            with allure.step('2. 校验新创建的分组是否在列表中展示'):
                check.is_true(self._is_group_in_list(test_group_name), f"❌ 新创建的分组未在列表中出现: '{test_group_name}'")
            with allure.step('3. 执行删除该新建分组操作'):
                del_result = self.tagGroupPage.delete_group_or_all_groups_flow(group_name=test_group_name)
                check.is_true(del_result, f"❌ 删除分组流程执行失败: '{test_group_name}'")
            with allure.step('4. 校验删除后分组已从列表中完全移除'):
                check.is_false(self._is_group_in_list(test_group_name), f"❌ 已删除的分组依然存在于列表中: '{test_group_name}'")
        finally:
            with allure.step('5. 环境恢复：如果依然残留该测试分组则执行兜底删除'):
                self._cleanup_group(test_group_name)


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('删除分组')
    @allure.title('批量清空所有好友分组并校验列表为空-状态：已完成')
    @pytest.mark.destructive
    def test_delete_all_contact_groups(self):
        """测试批量清空所有好友分组，校验列表清空后的状态"""
        test_group_1 = f'批量组1_{int(time.time())}'
        test_group_2 = f'批量组2_{int(time.time())}'
        try:
            with allure.step(f"1. 预先创建测试分组1 '{test_group_1}'"):
                self._create_subgroup_and_save(test_group_1, wait_toast=False)
            with allure.step(f"2. 预先创建测试分组2 '{test_group_2}'"):
                self._create_subgroup_and_save(test_group_2, wait_toast=False)
            with allure.step('3. 校验测试分组是否均已成功展示'):
                check.is_true(self._is_group_in_list(test_group_1), f"❌ 预先创建的分组1未在列表中出现: '{test_group_1}'")
                check.is_true(self._is_group_in_list(test_group_2), f"❌ 预先创建的分组2未在列表中出现: '{test_group_2}'")
            with allure.step('4. 执行批量清空所有分组操作'):
                del_all_result = self.tagGroupPage.delete_group_or_all_groups_flow(is_all=True)
                check.is_true(del_all_result, '❌ 批量清空所有分组流执行失败')
            with allure.step('5. 校验列表是否已完全清空'):
                self.tagGroupPage.wait_for_group_list_page_load()
                remaining_names = self.tagGroupPage.get_group_tag_names(timeout=1, raise_exception=False)
                check.equal(len(remaining_names), 0, f'❌ 批量删除后列表中依然残留分组: {remaining_names}')
        finally:
            with allure.step('6. 环境恢复：若仍有残留则强制清空'):
                remaining = self.tagGroupPage.get_group_tag_names(timeout=1, raise_exception=False)
                if remaining:
                    self.tagGroupPage.delete_group_or_all_groups_flow(is_all=True)


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('分组边界')
    @allure.title('FD_GROUP_TAG_002 - 分组名称长度 30 字上限边界参数化校验-状态：已完成')
    @pytest.mark.parametrize('input_length, expected_length', [
        pytest.param(29, 29, id='29字-正常'),
        pytest.param(30, 30, id='30字-上限'), 
        pytest.param(31, 30, id='31字-超限截断')
        ])
    def test_group_name_length_limit_parametrize(self, input_length: int, expected_length: int):
        """参数化验证分组名称输入 30 字上限限制及截断落库"""
        unique_prefix = f'qa{time.time_ns() % 100000}_'
        needed_len = input_length - len(unique_prefix)
        raw_name = (unique_prefix + '组' * needed_len)[:input_length]
        expected_name = raw_name[:expected_length]
        try:
            with allure.step('1. 进入新建分组页'):
                self.tagGroupPage.wait_for_group_list_page_load()
                self.tagGroupPage.click_add_subgroup()
            with allure.step(f'2. 输入 {input_length} 字名称，校验实际输入框截断保留 {expected_length} 字'):
                self.tagGroupPage.input_subgroup_name(raw_name)
                actual_input = self.tagGroupPage.get_subgroup_name_input_text()
                check.equal(len(actual_input), expected_length, f'❌ 分组名称长度截断不匹配，实际保留: {len(actual_input)}')
                check.equal(actual_input, expected_name, f"❌ 分组名称内容不匹配，实际: '{actual_input}'")
            with allure.step('3. 点击保存按钮并校验分组列表中成功渲染'):
                self.tagGroupPage.click_save_group()
                check.is_true(self._is_group_in_list(expected_name), f"❌ 保存后分组未在列表中出现: '{expected_name}'")
        finally:
            with allure.step('4. 环境恢复：如果成功保存则删除该测试分组'):
                self._cleanup_group(expected_name)


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('分组异常处理')
    @allure.title('FD_GROUP_TAG_003 - 尝试创建重复名称分组的拦截校验-状态：已完成')
    def test_duplicate_group_name_interception(self):
        """测试连续创建相同名称的分组，校验系统 Toast 重名拦截及安全退出"""
        duplicate_name = f'重名测试_{int(time.time())}'
        try:
            with allure.step('1. 先创建一个基础分组'):
                toast_save = self._create_subgroup_and_save(duplicate_name)
                check.is_true(toast_save, '❌ 基础分组未收到保存成功的 Toast 提示')
            with allure.step('2. 再次尝试创建同名分组，校验重名拦截 Toast'):
                self.tagGroupPage.wait_for_group_list_page_load()
                self.tagGroupPage.click_add_subgroup()
                self.tagGroupPage.input_subgroup_name(duplicate_name)
                self.tagGroupPage.click_save_group()
                toast_dup = self.tagGroupPage.get_toast('分组名已存在！', timeout=2)
                check.is_true(toast_dup, '❌ 未收到 [分组名已存在！] 重复拦截 Toast')
        finally:
            with allure.step('3. 环境清理：退出当前重名编辑页，并删除创建的测试分组'):
                self._cleanup_group(duplicate_name)