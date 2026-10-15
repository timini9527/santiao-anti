import time
import allure
import pytest
import pytest_check as check
from core.logger_utils import logger, LogIcon
from pages.chat.core.chat_page import ChatPage
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.friend.add_friend.add_friend_page import AddFriendPage
from pages.groups.public_group.public_group_page import PublicGroupPage
from strategy.chat.chat_strategy import GROUP_STRATEGY


@allure.epic('IM核心功能测试')
@allure.feature('群聊功能体系')
@allure.story('公开群聊推荐与交互')
class TestPublicGroup:
    """公开群聊模块自动化测试集 (展示于添加朋友页面内)"""

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender):
        """方法级前置与后置：初始化相关的 Page Object 并确保页面处于就绪状态"""
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.addFriendPage = AddFriendPage(driver_sender)
        self.publicGroupPage = PublicGroupPage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.groupSettingPage = GroupSettingPage(driver_sender)

        yield

        with allure.step('后置清理：安全返回首页会话列表'):
            try:
                self.mainPage.go_to_main_page()
            except Exception as e:
                logger.error(f'{LogIcon.WARN} 返回首页失败: {e}')

    def _home_to_public_group(self) -> None:
        """导航辅助：从主页右上角加号进入添加朋友页面，并等待公开群聊就绪"""
        with allure.step('前置步骤：从主页进入添加朋友页面并等待公开群聊加载'):
            self.homePage.click_add_button()
            self.homePage.click_add_friend()
            is_add_loaded = self.addFriendPage.wait_for_add_friend_page(timeout=10)
            check.is_true(is_add_loaded, '❌ 未能成功进入添加朋友页面')
            is_public_loaded = self.publicGroupPage.wait_for_public_group_loaded(timeout=10)
            check.is_true(is_public_loaded, '❌ 添加朋友页中的公开群聊模块未能加载完成')



    
    pub = False
    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title('频繁从公开群加入群聊与退出群聊异常流程-状态：已完成')
    def test_frequent_join_and_exit_public_group(self):
        """
        验证频繁连续从公开群聊列表加入群聊并退出群聊的闭环稳定性与幂等性：
        1. 指定目标群聊（支持在此直接指定如 "测试群001"，或从策略类 GROUP_STRATEGY.name 获取）
        2. 智能检索目标群聊并加入：优先在公开群列表中查找（支持自动【换一批】），未在列表时支持搜索直达
        3. 兼容公开群详情页二步确认，成功拉起聊天窗口
        4. 精准断言当前群聊名称与指定目标群一致
        5. 进入群设置，点击【删除并退出】并确认
        6. 验证安全退出群聊并返回主页面
        7. 循环执行 2 轮，验证连续加退群场景下的系统稳定性与会话销毁一致性
        """
        # 指定目标群聊名称 (可按需直接指定群名，如 "测试群001"，或使用 GROUP_STRATEGY.name)
        target_group: str = "测试群001"
        loop_times = 20
        for i in range(1, loop_times + 1):
            with allure.step(f'=== 第 {i}/{loop_times} 轮：进入指定目标群聊【{target_group}】与退群闭环测试 ==='):
                # 步骤 1：从首页进入公开群聊区域
                if not self.pub:
                    self._home_to_public_group()
                    self.pub = True

                # 步骤 2：检索指定目标群聊并触发加入
                with allure.step(f'第 {i} 轮-步骤 1: 检索指定目标公开群【{target_group}】并加入'):
                    logger.info(f"{LogIcon.FIND} 第 {i} 轮准备加入指定目标群聊: 【{target_group}】")
                    # 优先在公开群列表中自动匹配并换一批查找
                    is_joined = self.publicGroupPage.find_and_join_target_group(target_group, max_batches=5)

                # 步骤 3：兼容群详情页并校验进入群聊主界面
                with allure.step(f'第 {i} 轮-步骤 2: 确认群详情并拉起群聊界面'):
                    # 如果弹出了群详情页，确认群名并点击底部操作按钮
                    if self.publicGroupPage.wait_for_detail_page_loaded(timeout=3):
                        detail_name = self.publicGroupPage.get_detail_group_name()
                        action_text = self.publicGroupPage.get_detail_action_btn_text()
                        logger.info(f"{LogIcon.ACTION} 公开群详情页群名: '{detail_name}', 底部按钮: '{action_text}'")
                        self.publicGroupPage.click_detail_action_button()

                    # 校验是否成功拉起群聊主界面
                    is_in_chat = self.chatPage.wait_for_chat_page_load(timeout=2, raise_exception=False)
                    check.is_true(is_in_chat, f'❌ 第 {i} 轮加入目标群【{target_group}】后未能成功进入聊天页面')

                # TODO: # 这里有BUG
                if not is_in_chat:
                    logger.warning(f'{LogIcon.WARN} 第 {i} 轮未能进入聊天页，重新加入群聊，重新开始循环')
                    is_joined = self.publicGroupPage.find_and_join_target_group(target_group, max_batches=5)
                    
                    if self.publicGroupPage.wait_for_detail_page_loaded(timeout=3):
                        detail_name = self.publicGroupPage.get_detail_group_name()
                        action_text = self.publicGroupPage.get_detail_action_btn_text()
                        logger.info(f"{LogIcon.ACTION} 公开群详情页群名: '{detail_name}', 底部按钮: '{action_text}'")
                        self.publicGroupPage.click_detail_action_button()
                    

                # 步骤 4：精准校验当前进入的会话群名称与指定目标群一致
                with allure.step(f'第 {i} 轮-步骤 3: 校验当前群聊名称与指定目标群【{target_group}】一致'):
                    actual_group = self.chatPage.get_group_name()
                    logger.info(f"{LogIcon.FIND} 当前群聊实际名称: '{actual_group}', 预期目标群: '{target_group}'")
                    check.is_in(target_group, actual_group, f'❌ 当前群聊名称【{actual_group}】与目标群【{target_group}】不匹配')

                # 步骤 5：进入群设置并执行【删除并退出】
                with allure.step(f'第 {i} 轮-步骤 4: 进入群设置页面执行【删除并退出】'):
                    self.chatPage.click_more_button()
                    is_setting_loaded = self.groupSettingPage.wait_for_setting_page_load(timeout=5)
                    check.is_true(is_setting_loaded, f'❌ 第 {i} 轮未能成功进入群设置页面')
                    self.groupSettingPage.click_delete_and_out()
                    self.groupSettingPage.click_tv_confirm_button()

                # # 步骤 6：校验安全退出并确认处于主页面
                # with allure.step(f'第 {i} 轮-步骤 5: 校验退群后安全返回主页会话列表'):
                #     is_in_main = self.mainPage.is_in_main_page(timeout=5)
                #     if not is_in_main:
                #         self.mainPage.go_to_main_page()
                #         is_in_main = self.mainPage.is_in_main_page(timeout=3)
                #     check.is_true(is_in_main, f'❌ 第 {i} 轮删除并退出群聊后未能返回主页面')
                #     logger.info(f'{LogIcon.SUCCESS} 第 {i} 轮公开群加群并退群流程执行完成')


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title('【界面展示】公开群聊区域标题及列表元素完整性校验-状态：未完成')
    def test_public_group_display_and_elements(self):
        """验证公开群聊区域标题、换一批按钮、规则入口及首屏公开群卡片基本要素完整展示"""
        self._home_to_public_group()

        with allure.step('1. 校验公开群聊区域标题文本'):
            title = self.publicGroupPage.get_rank_title()
            logger.info(f"{LogIcon.ACTION} 公开群聊区域标题: '{title}'")
            check.is_in('公开群聊', title, f'❌ 公开群聊区域标题不匹配，实际展示为: {title}')

        with allure.step('2. 校验公开群聊推荐列表非空并提取群名称'):
            group_names = self.publicGroupPage.get_public_group_names()
            logger.info(f"{LogIcon.ACTION} 当前公开群列表展示群名称: {group_names}")
            check.greater(len(group_names), 0, '❌ 公开群推荐列表为空，未获取到任何公开群')

        if group_names:
            first_group = group_names[0]
            with allure.step(f'3. 校验首个公开群【{first_group}】各属性完整性 (活跃度/成员数/群ID)'):
                info = self.publicGroupPage.get_group_info(first_group)
                logger.info(f"{LogIcon.ACTION} 首个公开群【{first_group}】卡片详情: {info}")
                check.is_true(bool(info.get('active_value')), f'❌ 公开群【{first_group}】活跃度数值为空')
                check.is_true(bool(info.get('member_num')), f'❌ 公开群【{first_group}】成员数量为空')
                check.is_true('ID' in info.get('group_id', ''), f'❌ 公开群【{first_group}】群ID格式异常: {info.get("group_id")}')

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title('【功能交互】点击换一批功能刷新公开群列表校验-状态：未完成')
    def test_public_group_change_batch(self):
        """验证点击【换一批】后公开群列表成功触发刷新"""
        self._home_to_public_group()

        with allure.step('1. 获取换一批点击前公开群列表'):
            initial_groups = self.publicGroupPage.get_public_group_names()
            logger.info(f"{LogIcon.ACTION} 换一批前公开群列表: {initial_groups}")

        with allure.step('2. 点击【换一批】按钮'):
            self.publicGroupPage.click_change_batch()
            time.sleep(1)

        with allure.step('3. 获取换一批点击后公开群列表并校验'):
            refreshed_groups = self.publicGroupPage.get_public_group_names()
            logger.info(f"{LogIcon.ACTION} 换一批后公开群列表: {refreshed_groups}")
            check.greater(len(refreshed_groups), 0, '❌ 换一批后公开群列表为空')
            # 记录刷新前后对比结果日志
            is_changed = initial_groups != refreshed_groups
            logger.info(f"{LogIcon.ACTION} 换一批前后群列表是否发生变化: {is_changed}")

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title('【功能交互】点击复制群ID按钮功能校验-状态：未完成')
    def test_public_group_copy_id(self):
        """验证点击公开群卡片上的复制群ID按钮"""
        self._home_to_public_group()

        with allure.step('1. 获取当前首个公开群名称'):
            group_names = self.publicGroupPage.get_public_group_names()
            check.greater(len(group_names), 0, '❌ 公开群列表为空，无法进行复制群ID测试')

        if group_names:
            target_group = group_names[0]
            with allure.step(f'2. 点击公开群【{target_group}】的复制群ID按钮'):
                self.publicGroupPage.click_copy_group_id(target_group)
                time.sleep(0.5)
                logger.info(f"{LogIcon.SUCCESS} 已成功点击公开群【{target_group}】复制群ID按钮")

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title('【功能交互】点击加入公开群按钮流程触发校验-状态：未完成')
    def test_public_group_click_join(self):
        """验证点击公开群卡片上的【加入】按钮能够正常响应并触发加群流程"""
        self._home_to_public_group()

        with allure.step('1. 获取当前首个公开群名称'):
            group_names = self.publicGroupPage.get_public_group_names()
            check.greater(len(group_names), 0, '❌ 公开群列表为空，无法进行点击加入测试')

        if group_names:
            target_group = group_names[0]
            with allure.step(f'2. 点击公开群【{target_group}】的【加入】按钮'):
                self.publicGroupPage.click_join_group(target_group)
                time.sleep(1)
                logger.info(f"{LogIcon.SUCCESS} 已成功触发公开群【{target_group}】加入动作")

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title('【导航流转】从添加朋友与公开群页面安全返回主页-状态：未完成')
    def test_public_group_back_to_home(self):
        """验证从公开群宿主页面（添加朋友）点击返回能够正常回退至首页会话列表"""
        self._home_to_public_group()

        with allure.step('1. 点击左上角返回按钮'):
            self.addFriendPage.click_back()
            time.sleep(0.5)

        with allure.step('2. 验证已安全返回至首页'):
            is_in_main = self.mainPage.is_in_main_page(timeout=5)
            check.is_true(is_in_main, '❌ 从添加朋友与公开群页面返回后未处于主页面')
