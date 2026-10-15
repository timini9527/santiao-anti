from pages.main.main_page import MainPage
import pytest
import allure
import yaml
import time
import os
from appium.webdriver.common.appiumby import AppiumBy
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.setting.chat_setting_page import ChatSettingPage
from pages.report.report_page import ReportPage
from strategy.chat.chat_strategy import PRIVATE_USER1
from core.logger_utils import logger, LogIcon

@allure.epic('IM核心功能测试')
@allure.feature('投诉模块提取')
@allure.story('自动遍历提取全量投诉树结构')
class TestExtractReportTree:
    """自动化提取整个投诉菜单层级并导出为 YAML"""

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        self.driver = driver_sender
        self.chatListPage = ChatListPage(driver_sender)
        self.chatSettingPage = ChatSettingPage(driver_sender)
        self.reportPage = ReportPage(driver_sender)
        with allure.step('前置准备：进入目标好友的单聊会话并进入设置-投诉'):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.chatListPage.click_more_button()
            self.chatSettingPage.wait_for_setting_page_load()
            self.chatSettingPage.click_report()
            time.sleep(2)
        yield
        try:
            MainPage(self.driver).go_to_main_page()
        except Exception:
            pass

    @pytest.mark.skip(reason='已完成提取，用于参考')
    @allure.title('自动遍历提取全量投诉树结构-状态：已完成')
    def test_extract_report_tree(self):
        """完全按照用户指定的层级遍历逻辑重构"""

        def safe_click_back():
            """安全的返回方法：点击 UI 返回按钮并验证页面是否真正发生了改变"""
            before_texts = [tv.text for tv in self.driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.TextView') if tv.text]
            for _ in range(3):
                try:
                    self.reportPage.click_back()
                    time.sleep(1.5)
                    after_texts = [tv.text for tv in self.driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.TextView') if tv.text]
                    if before_texts != after_texts:
                        return
                    logger.warning(f'{LogIcon.WARN} 点击了返回按钮，但页面没变，重试...')
                    time.sleep(1)
                except Exception as e:
                    logger.warning(f'{LogIcon.WARN} 点击返回抛出异常: {e}')
                    time.sleep(1)
            logger.error(f'{LogIcon.FAIL} 致命错误：多次尝试 UI 返回失败，强制终止！')
            raise RuntimeError('无法执行返回操作！')

        def dfs(current_level, parent_name=''):
            end_time = time.time() + 5.0
            options = []
            ignore_texts = ['投诉', '返回', '提交', '下一步', parent_name, '请选择投诉该账号的原因：', '请选择投诉该群的原因：', '请选择投诉原因']
            while time.time() < end_time:
                if self.driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.EditText'):
                    break
                text_views = self.driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.TextView')
                temp_options = []
                if len(text_views) > 1:
                    first_text = text_views[1].text.strip()
                    temp_ignore = ignore_texts.copy()
                    if first_text not in temp_ignore:
                        temp_ignore.append(first_text)
                else:
                    temp_ignore = ignore_texts
                for tv in text_views:
                    text = tv.text.strip()
                    if text and text not in temp_ignore:
                        if text not in temp_options:
                            temp_options.append(text)
                if temp_options:
                    options = temp_options
                    break
                time.sleep(0.3)
            if not options:
                return []
            result_dict = {}
            leaf_list = []
            for i, option in enumerate(options):
                logger.info(f'{LogIcon.ACTION} [Level {current_level}] 探测选项: {option}')
                Level_texts = self.driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.TextView')
                before_texts = [tv.text for tv in Level_texts if tv.text]
                logger.info(f'{LogIcon.ACTION} [Level {current_level}] 第 {current_level} 级菜单: {before_texts}')
                locator = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{option}")')
                try:
                    el = self.driver.find_element(*locator)
                    el.click()
                    time.sleep(1.0)
                    after_texts = [tv.text for tv in self.driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.TextView') if tv.text]
                    if self.driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.EditText') or before_texts != after_texts:
                        pass
                    else:
                        logger.warning(f"{LogIcon.WARN} 点击 '{option}' 后页面未变化，尝试二次重试点击...")
                        el = self.driver.find_element(*locator)
                        el.click()
                        time.sleep(1.0)
                except Exception as e:
                    logger.warning(f"{LogIcon.WARN} 无法点击 '{option}': {e}")
                    continue
                elements = self.driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.EditText')
                if len(elements) > 0:
                    logger.info(f"{LogIcon.SUCCESS} 点击选项 '{option}' 已到达末级节点，成功进入内容填写页面")
                    safe_click_back()
                    leaf_list.append(option)
                    continue
                else:
                    Level_texts_after = self.driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.TextView')
                    after_texts = [tv.text for tv in Level_texts_after if tv.text]
                    if before_texts == after_texts:
                        logger.info(f"{LogIcon.FAIL} 点击 '{option}' 页面无变化，判定为静态节点。")
                        leaf_list.append(option)
                        continue
                    sub_tree = dfs(current_level + 1, option)
                    if sub_tree:
                        result_dict[option] = sub_tree
                    else:
                        result_dict[option] = []
                    safe_click_back()
            if not result_dict and leaf_list:
                return leaf_list
            elif result_dict and (not leaf_list):
                return result_dict
            else:
                for leaf in leaf_list:
                    result_dict[leaf] = []
                return result_dict
        logger.info(f'{LogIcon.ACTION} 开始按节点层级递归抓取...')
        tree = dfs(1)
        yaml_path = os.path.join(os.path.dirname(__file__), 'report_tree_output.yaml')
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(tree, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        logger.info(f"{LogIcon.SUCCESS} 抓取大功告成！文件已保存至: {yaml_path}")
        logger.info(f"{LogIcon.SUCCESS} 抓取树结构详情:\n{yaml.dump(tree, allow_unicode=True, sort_keys=False)}")