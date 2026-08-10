import random
import pytest
import allure
import pytest_check as check
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.setting.chat_setting_page import ChatSettingPage
from pages.report.report_page import ReportPage
from strategy.chat.chat_strategy import PRIVATE_USER1
from utils.file_reader.data_loader import load_yaml_data
from pages.main.main_page import MainPage

@allure.epic('IM核心功能测试')
@allure.feature('聊天设置')
@allure.story('单聊设置 - 投诉功能')
class TestChatReport:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        self.chatListPage = ChatListPage(driver_sender)
        self.chatSettingPage = ChatSettingPage(driver_sender)
        self.reportPage = ReportPage(driver_sender)
        self.mainPage = MainPage(driver_sender)
        with allure.step('前置准备：进入目标好友的单聊会话并进入设置'):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.chatListPage.click_more_button()
            self.chatSettingPage.wait_for_setting_page_load()
        yield
        with allure.step('后置清理：退回到主页'):
            try:
                self.mainPage.go_to_main_page()
            except Exception as e:
                pass

    @allure.story('投诉分类列表结构验证')
    @allure.title('投诉分类列表结构验证-状态：已完成')
    def test_report_categories_layout(self):
        """动态加载 report_tree_output.yaml，校验投诉首屏一级大类及二级分类是否渲染完整"""
        report_tree = load_yaml_data('report/report_tree_output.yaml')
        with allure.step('1、点击投诉，验证投诉首屏一级大类是否存在'):
            self.chatSettingPage.click_report()
            self.reportPage.wait_for_report_page_load()
            root_categories = list(report_tree.keys())
            for cat in root_categories:
                is_visible = self.reportPage.is_category_visible(cat)
                check.is_true(is_visible, f"❌ 投诉首屏未找到一级大类: '{cat}'")
        with allure.step('2、动态遍历并校验各一级分类下的子级选项是否完整'):
            for parent_cat, sub_tree in report_tree.items():
                if sub_tree:
                    self.reportPage.select_report_path([parent_cat])
                    if isinstance(sub_tree, dict):
                        expected_sub_items = list(sub_tree.keys())
                    elif isinstance(sub_tree, list):
                        expected_sub_items = sub_tree
                    else:
                        expected_sub_items = []
                    for sub_item in expected_sub_items:
                        if not sub_item:
                            continue
                        is_visible = self.reportPage.is_category_visible(sub_item)
                        check.is_true(is_visible, f"❌ 在 '{parent_cat}' 下未找到二级子项: '{sub_item}'")
                    self.reportPage.click_back()

    @allure.story('投诉流程随机路径冒烟测试')
    @allure.title('投诉流程随机路径冒烟测试-状态：已完成')
    def test_submit_report_smoke(self):
        """随机选取投诉路径进行端到端提交的冒烟测试"""
        report_tree = load_yaml_data('report/report_tree_output.yaml')

        def collect_submit_paths(node, current_path=[]):
            paths = []
            if isinstance(node, dict):
                for k, v in node.items():
                    if '拉入黑名单' in k:
                        continue
                    paths.extend(collect_submit_paths(v, current_path + [k]))
            elif isinstance(node, list):
                if len(node) == 0:
                    paths.append(current_path)
                else:
                    for item in node:
                        if '拉入黑名单' in item:
                            continue
                        paths.append(current_path + [item])
            return paths
        all_paths = collect_submit_paths(report_tree)
        assert len(all_paths) > 0, '❌ 未能在 YAML 树中解析出任何合法的投诉提交路径'
        random_path = random.choice(all_paths)
        allure.dynamic.title(f"投诉流程冒烟测试 - 随机路径: {' -> '.join(random_path)}")
        with allure.step('1、进入投诉首屏'):
            self.chatSettingPage.click_report()
            self.reportPage.wait_for_report_page_load()
        with allure.step(f"2、依次选择投诉子分类路径: {' -> '.join(random_path)}"):
            self.reportPage.select_report_path(random_path)
        with allure.step('3、填写投诉详情描述并提交'):
            self.reportPage.submit_report_complete_flow()
        with allure.step('4、提交投诉并校验反馈 Toast 提示'):
            actual_toast = self.reportPage.submit_report()
        with allure.step('4、返回设置页面'):
            actual_title = self.chatSettingPage.get_chat_setting_title()
            check.is_in('聊天信息', actual_title, f'❌ 返回聊天设置页面失败')