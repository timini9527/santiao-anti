from pages.main.main_page import MainPage
import pytest
import allure
import yaml
import time
import os
from appium.webdriver.common.appiumby import AppiumBy
from pages.chat.chat_list_page import ChatListPage
from pages.chat.chat_setting_page import ChatSettingPage
from pages.report.report_page import ReportPage
from locators.report.report_locator import ReportLocator
from pages.chat.chat_strategy import PRIVATE_USER1
from core.logger_utils import logger

@allure.epic("IM核心功能测试")
@allure.feature("投诉模块提取")
@allure.story("自动遍历提取全量投诉树结构")
class TestExtractReportTree:
    """自动化提取整个投诉菜单层级并导出为 YAML"""

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        self.driver = driver_sender
        self.chatListPage = ChatListPage(driver_sender)
        self.chatSettingPage = ChatSettingPage(driver_sender)
        self.reportPage = ReportPage(driver_sender)
        
        # 前置条件：进入聊天，进入设置，点击投诉
        with allure.step("前置准备：进入目标好友的单聊会话并进入设置-投诉"):
            self.chatListPage.enter_chat(PRIVATE_USER1.name)
            self.chatListPage.click_more_button()
            self.chatSettingPage.wait_for_setting_page_load()
            self.chatSettingPage.click_report()
            
            # 等待第一级菜单加载
            time.sleep(2)
        yield
        
        # 后置清理
        try:
            MainPage(self.driver).go_to_main_page()
        except Exception:
            pass
    
    @pytest.mark.skip(reason="已完成提取，用于参考")
    def test_extract_report_tree(self):
        """完全按照用户指定的层级遍历逻辑重构"""
        
        def safe_click_back():
            """安全的返回方法：点击 UI 返回按钮并验证页面是否真正发生了改变"""
            before_texts = [tv.text for tv in self.driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.TextView') if tv.text]
            
            for _ in range(3):
                try:
                    # 绕过 BasePage 直接点击，防止频繁截图
                    el = self.driver.find_element(*ReportLocator.TOP_IV_BACK_BTN)
                    el.click()
                    time.sleep(1.5)
                    
                    after_texts = [tv.text for tv in self.driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.TextView') if tv.text]
                    if before_texts != after_texts:
                        return # 成功退回
                    
                    logger.warning("⚠️ 点击了返回按钮，但页面没变，重试...")
                    time.sleep(1)
                except Exception as e:
                    logger.warning(f"⚠️ 点击返回抛出异常: {e}")
                    time.sleep(1)
                    
            logger.error("❌ 致命错误：多次尝试 UI 返回失败，强制终止！")
            raise RuntimeError("无法执行返回操作！")

        def dfs(current_level, parent_name=""):
            # 动态探测当前页面加载，最长等待 5.0 秒，一旦检测到有效选项或输入框则立即进入后续流程
            end_time = time.time() + 5.0
            options = []
            ignore_texts = ["投诉", "返回", "提交", "下一步", parent_name, "请选择投诉该账号的原因：", "请选择投诉该群的原因：", "请选择投诉原因"]
            
            while time.time() < end_time:
                # 若已到达输入框页，立即跳出等待
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
            
            # 依次点击当前层级的每一个选项
            for i, option in enumerate(options):
                logger.info(f"👉 [Level {current_level}] 探测选项: {option}")

                Level_texts = self.driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.TextView')
                
                before_texts = [tv.text for tv in Level_texts if tv.text]
                logger.info(f"👉 [Level {current_level}] 第 {current_level} 级菜单: {before_texts}")
                
                # 点击选项进入下一页
                locator = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{option}")')
                try:
                    el = self.driver.find_element(*locator)
                    el.click()
                    time.sleep(1.0)
                    
                    # 动态判断页面是否已发生跳转（出现输入框或文本内容改变）
                    after_texts = [tv.text for tv in self.driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.TextView') if tv.text]
                    if self.driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.EditText') or before_texts != after_texts:
                        pass
                    else:
                        logger.warning(f"⚠️ 点击 '{option}' 后页面未变化，尝试二次重试点击...")
                        el = self.driver.find_element(*locator)
                        el.click()
                        time.sleep(1.0)
                except Exception as e:
                    logger.warning(f"⚠️ 无法点击 '{option}': {e}")
                    continue
                    
                # 检查进入的新页面是否是“填写内容页”（即存在 EditText）
                elements = self.driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.EditText')
                if len(elements) > 0:
                    # 进入到填写页面后，说明该具体子项已到底
                    logger.info(f"✅ '{option}' 到底了！进入了填写内容页。")
                    
                    # 退回到刚才那一层
                    safe_click_back()
                    
                    # 记录为叶子节点，并继续遍历这一层剩余的同级选项
                    leaf_list.append(option)
                    continue
                    
                else:
                    # 没有进入填写内容页，判断是否真的跳到了子菜单
                    Level_texts_after = self.driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.TextView')
                    after_texts = [tv.text for tv in Level_texts_after if tv.text]
                    if before_texts == after_texts:
                        # 页面根本没变，说明是个废弃/静态节点
                        logger.info(f"🛑 点击 '{option}' 页面无变化，判定为静态节点。")
                        leaf_list.append(option)
                        continue
                        
                    # 规则1：页面变了，说明进入了子菜单页，递归获取所有的子节点数据
                    sub_tree = dfs(current_level + 1, option)
                    
                    if sub_tree:
                        result_dict[option] = sub_tree
                    else:
                        result_dict[option] = [] # 保证每一个节点都有数据
                        
                    # 从子菜单页退回到当前页，继续循环下一个节点
                    safe_click_back()
                    
            # 整合这一层的数据结构
            if not result_dict and leaf_list:
                # 这一层全是叶子节点，返回列表
                return leaf_list
            elif result_dict and not leaf_list:
                # 这一层全是子菜单，返回字典
                return result_dict
            else:
                # 既有子菜单又有叶子节点（混合型），把叶子节点也写进字典里保证结构统一
                for leaf in leaf_list:
                    result_dict[leaf] = [] 
                return result_dict

        # 开始遍历
        logger.info("🚀 开始按节点层级递归抓取...")
        tree = dfs(1)
        
        # 写入 YAML 文件
        yaml_path = os.path.join(os.path.dirname(__file__), "report_tree_output.yaml")
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(tree, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            
        logger.info(f"🎉 抓取大功告成！文件已保存至: {yaml_path}")
        print("\n" + "="*40 + "\n")
        print(yaml.dump(tree, allow_unicode=True, sort_keys=False))
        print("\n" + "="*40 + "\n")
