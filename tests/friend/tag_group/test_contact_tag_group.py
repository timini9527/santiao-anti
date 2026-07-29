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

RECEIVER_NAME = "极速自动化"


@allure.epic("通讯录模块")
@allure.feature("好友分组与标签管理")
class TestContactTagGroup:
    """微信好友分组/标签功能自动化测试集"""

    @pytest.fixture(scope="class", autouse=True)
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
        """用例级别前置与后置：初始化页面对象，后置确保停留在好友页面"""
        # S 端 (发送方 Sender / 操作方)
        self.mainPageS = MainPage(driver_sender)
        self.homePageS = HomePage(driver_sender)
        self.contactSelectPageS = ContactSelectPage(driver_sender)
        self.contactDetailPageS = ContactDetailPage(driver_sender)
        self.tagGroupPageS = ContactTagGroupPage(driver_sender)
        self.tagGroupPage = self.tagGroupPageS

        yield
        try:
            self.homePageS.click_friend()
        except Exception as e:
            logger.error(f"⚠️ [Teardown] 返回好友页面失败: {e}")


    def _go_to_group_list_page(self):
        """前置辅助函数：导航至好友分组/标签管理列表页"""
        # 进入通讯录/好友详情中转
        self.contactDetailPage.wait_for_detail_page_load()

    @allure.story("新建分组")
    @allure.title("FD_GROUP_TAG_001 - 正向创建好友分组、添加成员并校验展示")
    def test_create_and_delete_contact_group_normal(self):
        """测试创建新好友分组，校验保存后正确在分组列表显示，并测试删除销毁流程"""
        test_group_name = f"自动化组_{int(time.time())}"
        
        try:
            with allure.step("1. 进入分组管理页并点击新建"):
                self.tagGroupPage.wait_for_group_list_page_load()
                self.tagGroupPage.click_create_new_group()

            with allure.step(f"2. 输入分组名称 '{test_group_name}' 并保存"):
                self.tagGroupPage.input_group_name(test_group_name)
                self.tagGroupPage.click_save_group()
                toast = self.tagGroupPage.get_toast("创建成功", timeout=10)
                check.is_true(toast, "❌ 未收到分组创建成功的 Toast 提示")

            with allure.step("3. 校验新创建的分组是否在列表中展示"):
                self.tagGroupPage.wait_for_group_list_page_load()
                group_names = self.tagGroupPage.get_group_names()
                check.is_in(test_group_name, group_names, f"❌ 新创建的分组未在列表中出现: '{test_group_name}'")

        finally:
            with allure.step("4. 环境恢复：点击进入新建的分组并执行删除"):
                if self.tagGroupPage.click_group_by_name(test_group_name):
                    self.tagGroupPage.delete_group_flow()
                    toast_del = self.tagGroupPage.get_toast("删除成功", timeout=10)
                    check.is_true(toast_del, "❌ 未收到删除成功的 Toast 提示")
                self.tagGroupPage.click_back()

    @allure.story("删除分组")
    @allure.title("FD_GROUP_TAG_005 - 正向删除好友分组并校验展示")
    @pytest.mark.destructive
    def test_delete_contact_group_normal(self):
        """测试删除好友分组，校验保存后正确在分组列表显示，并测试删除销毁流程"""
        test_group_name = f"自动化组_{int(time.time())}"
        
        try:
            with allure.step("1. 进入管理分组页面并点击【添加分组】"):
                self.tagGroupPage.wait_for_group_list_page_load(page_title="1")
                self.tagGroupPage.click_add_subgroup()

            with allure.step(f"2. 输入分组名称 '{test_group_name}' 并保存"):
                self.tagGroupPage.input_subgroup_name(test_group_name)
                self.tagGroupPage.click_save_group()
                toast = self.tagGroupPage.get_toast("保存成功", timeout=10)
                check.is_true(toast, "❌ 未收到分组保存成功的 Toast 提示")

            with allure.step("3. 校验新创建的分组是否在列表中展示"):
                self.tagGroupPage.wait_for_group_list_page_load(page_title="1")
                group_names = self.tagGroupPage.get_group_tag_names()
                check.is_in(test_group_name, group_names, f"❌ 新创建的分组未在列表中出现: '{test_group_name}'")

            with allure.step("4. 执行删除该新建分组操作"):
                del_result = self.tagGroupPage.delete_group_or_all_groups_flow(group_name=test_group_name)
                check.is_true(del_result, f"❌ 删除分组流程执行失败: '{test_group_name}'")

            with allure.step("5. 校验删除后分组已从列表中移除"):
                self.tagGroupPage.wait_for_group_list_page_load(page_title="1")
                latest_names = self.tagGroupPage.get_group_tag_names()
                check.is_not_in(test_group_name, latest_names, f"❌ 已删除的分组依然存在于列表中: '{test_group_name}'")

        finally:
            with allure.step("6. 环境恢复：如果依然残留该测试分组则执行兜底删除"):
                current_names = self.tagGroupPage.get_group_tag_names(timeout=2)
                if test_group_name in current_names:
                    self.tagGroupPage.delete_group_or_all_groups_flow(group_name=test_group_name)

    @allure.story("删除分组")
    @allure.title("批量清空所有好友分组并校验列表为空")
    @pytest.mark.destructive
    def test_delete_all_contact_groups(self):
        """测试批量清空所有好友分组，校验列表清空后的状态"""
        test_group_1 = f"批量组1_{int(time.time())}"
        test_group_2 = f"批量组2_{int(time.time())}"

        try:
            # with allure.step("1. 创建第 1 个测试分组"):
            #     self.tagGroupPage.wait_for_group_list_page_load(page_title="1")
            #     self.tagGroupPage.click_add_subgroup()
            #     self.tagGroupPage.input_subgroup_name(test_group_1)
            #     self.tagGroupPage.click_save_group()

            # with allure.step("2. 创建第 2 个测试分组"):
            #     self.tagGroupPage.wait_for_group_list_page_load(page_title="1")
            #     self.tagGroupPage.click_add_subgroup()
            #     self.tagGroupPage.input_subgroup_name(test_group_2)
            #     self.tagGroupPage.click_save_group()

            with allure.step("3. 校验测试分组是否均已成功展示"):
                self.tagGroupPage.wait_for_group_list_page_load(page_title="0")
                group_names = self.tagGroupPage.get_group_tag_names()
                # check.is_in(test_group_1, group_names, f"❌ 测试分组 1 未出现在列表中: '{test_group_1}'")
                # check.is_in(test_group_2, group_names, f"❌ 测试分组 2 未出现在列表中: '{test_group_2}'")

            with allure.step("4. 执行批量清空所有分组操作"):
                del_all_result = self.tagGroupPage.delete_group_or_all_groups_flow(is_all=True)
                check.is_true(del_all_result, "❌ 批量清空所有分组流执行失败")

            with allure.step("5. 校验列表是否已完全清空"):
                self.tagGroupPage.wait_for_group_list_page_load(page_title="0")
                remaining_names = self.tagGroupPage.get_group_tag_names(timeout=3)
                check.equal(len(remaining_names), 0, f"❌ 批量删除后列表中依然残留分组: {remaining_names}")

        finally:
            with allure.step("6. 环境恢复：若仍有残留则强制清空"):
                remaining = self.tagGroupPage.get_group_tag_names(timeout=2)
                if remaining:
                    self.tagGroupPage.delete_group_or_all_groups_flow(is_all=True)


    @allure.story("分组边界")
    @allure.title("FD_GROUP_TAG_002 - 分组名称长度边界参数化校验")
    @pytest.mark.parametrize(
        "input_length, expected_length",
        [
            (10, 10),
            (15, 15),
            (16, 15),
        ],
        ids=["10字-正常", "15字-上限", "16字-超限截断"]
    )
    def test_group_name_length_limit_parametrize(self, input_length: int, expected_length: int):
        """参数化验证分组名称输入长度上限限制"""
        raw_name = ("组" + ("x" * input_length))[:input_length]
        expected_name = raw_name[:expected_length]

        try:
            with allure.step("1. 进入新建分组页"):
                self.tagGroupPage.wait_for_group_list_page_load()
                self.tagGroupPage.click_create_new_group()

            with allure.step(f"2. 输入 {input_length} 字名称，校验实际输入框截断保留 {expected_length} 字"):
                self.tagGroupPage.input_group_name(raw_name)
                actual_input = self.tagGroupPage.get_input_group_name()
                check.equal(len(actual_input), expected_length, f"❌ 分组名称长度截断不匹配，实际保留: {len(actual_input)}")
                check.equal(actual_input, expected_name, f"❌ 分组名称内容不匹配，实际: '{actual_input}'")
        finally:
            with allure.step("3. 取消并安全返回列表页"):
                self.tagGroupPage.click_back()

    @allure.story("分组异常处理")
    @allure.title("FD_GROUP_TAG_003 - 尝试创建重复名称分组的拦截校验")
    def test_duplicate_group_name_interception(self):
        """测试连续创建相同名称的分组，校验系统弹窗/Toast 重名拦截"""
        duplicate_name = f"重名测试_{int(time.time())}"

        try:
            with allure.step("1. 先创建一个基础分组"):
                self.tagGroupPage.wait_for_group_list_page_load()
                self.tagGroupPage.click_create_new_group()
                self.tagGroupPage.input_group_name(duplicate_name)
                self.tagGroupPage.click_save_group()
                self.tagGroupPage.get_toast("创建成功", timeout=10)

            with allure.step("2. 再次尝试创建同名分组，校验拦截"):
                self.tagGroupPage.wait_for_group_list_page_load()
                self.tagGroupPage.click_create_new_group()
                self.tagGroupPage.input_group_name(duplicate_name)
                self.tagGroupPage.click_save_group()
                
                toast_dup = self.tagGroupPage.get_toast("分组名称已存在", timeout=10)
                check.is_true(toast_dup, "❌ 未收到分组名称重复拦截 Toast")

        finally:
            with allure.step("3. 清理测试数据"):
                self.tagGroupPage.click_back()
                if self.tagGroupPage.click_group_by_name(duplicate_name):
                    self.tagGroupPage.delete_group_flow()
                self.tagGroupPage.click_back()
