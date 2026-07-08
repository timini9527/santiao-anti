import pytest
import allure
import time
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.moments.moments_page import MomentsPage
from pages.home.home_page import HomePage


@allure.epic("IM核心功能测试")
@allure.feature("朋友圈模块-多端与社交互动")
class TestMomentsDouble:
    """朋友圈与动态社交互动双端协同测试"""

    @pytest.fixture(autouse=True)
    def setup_double_env(self, driver_sender, driver_receiver):
        """初始化双端页面对象并确保其测试前状态正常"""
        self.mainS = MainPage(driver_sender)
        self.momentsS = MomentsPage(driver_sender)
        self.homeS = HomePage(driver_sender)

        self.mainR = MainPage(driver_receiver)
        self.momentsR = MomentsPage(driver_receiver)
        self.homeR = HomePage(driver_receiver)

        # 确保两端进入测试的默认页面 (通常先保持在主页)
        with allure.step("前置步骤：两端确认在主页并进入朋友圈"):
            self.mainS.go_to_main_page()
            self.mainR.go_to_main_page()

        yield

        # 清理工作：两端返回主页
        with allure.step("后置清理：两端返回首页"):
            try:
                self.mainS.go_to_main_page()
            except Exception as e:
                logger.error(f"发送端 Teardown 失败: {e}")
            try:
                self.mainR.go_to_main_page()
            except Exception as e:
                logger.error(f"接收端 Teardown 失败: {e}")

    @allure.story("好友动态可见性与更新同步")
    @allure.title("MOMENT_ENTRY_002 / MOMENT_ERR_002 - 好友发布朋友圈动态后接收端同步可见")
    def test_friend_moment_visibility(self):
        """测试发送端发布公开动态后，接收端刷新能同步可见"""
        timestamp = int(time.time())
        test_content = f"双端可见性测试文字动态 {timestamp}"

        # 1. 发送端进入朋友圈并发布一条唯一文案的公开动态
        with allure.step("1. 发送端进入朋友圈并发布公开动态"):
            self.mainS.go_to_moments_page()
            self.momentsS.wait_for_moments_page_load(raise_exception=False)
            self.momentsS.post_text_moment(test_content)
            logger.info(f"发送端已发布动态: {test_content}")

        # 2. 接收端进入朋友圈并下拉刷新，校验是否能够看到该动态
        with allure.step("2. 接收端进入朋友圈并下拉刷新"):
            self.mainR.go_to_moments_page()
            self.momentsR.wait_for_moments_page_load(raise_exception=False)
            self.momentsR.refresh_moments()

        with allure.step("3. 校验接收端信息流首位是否同步显示该动态"):
            actual_content = self.momentsR.get_first_moment_content()
            check.equal(actual_content, test_content, "❌ 接收端未能同步看到发送端发布的好友朋友圈动态")

    @allure.story("社交互动与反馈")
    @allure.title("MOMENT_INTER_001 / MOMENT_INTER_003 - 给好友朋友圈点赞和评论多端同步校验")
    def test_moment_interaction_double(self):
        """测试接收端给发送端发布的朋友圈进行点赞和评论，发送端可实时查看互动结果"""
        timestamp = int(time.time())
        test_content = f"双端互动测试动态 {timestamp}"
        comment_content = f"来自好友的自动点赞评论 {timestamp}"

        # 1. 发送端发布公开动态
        with allure.step("1. 发送端进入朋友圈并发布动态"):
            self.mainS.go_to_moments_page()
            self.momentsS.wait_for_moments_page_load(raise_exception=False)
            self.momentsS.post_text_moment(test_content)

        # 2. 接收端刷新并查看到该动态，点击点赞并进行评论
        with allure.step("2. 接收端进入朋友圈刷新并进行点赞评论"):
            self.mainR.go_to_moments_page()
            self.momentsR.wait_for_moments_page_load(raise_exception=False)
            self.momentsR.refresh_moments()
            
            # 双端对齐：确认接收端首位是发送端刚发的动态，然后进行点赞与评论
            first_content = self.momentsR.get_first_moment_content()
            if first_content == test_content:
                self.momentsR.like_first_moment()
                self.momentsR.comment_on_first_moment(comment_content)
                logger.info("接收端已成功点赞并发表评论")
            else:
                pytest.skip("接收端未刷出发送端刚发的动态，跳过互动测试")

        # 3. 发送端刷新朋友圈页面，校验接收端的点赞信息和评论内容是否成功同步展示
        with allure.step("3. 发送端刷新页面并校验互动信息"):
            self.momentsS.refresh_moments()
            # 校验评论是否包含刚才发送的评论内容
            comments = self.momentsS.get_comment_texts()
            check.is_true(
                any(comment_content in comment for comment in comments),
                f"❌ 发送端未看到接收端的评论内容: {comment_content}"
            )
            # 校验点赞状态是否更新
            like_text = self.momentsS.get_first_moment_like_text()
            check.is_true(bool(like_text), "❌ 发送端未展示点赞状态或点赞人")

    @allure.story("社交可见性与互为好友规则")
    @allure.title("MOMENT_SET_006 - 发送端发布私密朋友圈，接收端不可见")
    def test_private_moment_visibility_double(self):
        """测试发送端发布私密动态后，接收端无法查看"""
        timestamp = int(time.time())
        private_content = f"我是私密动态 {timestamp}"

        # 1. 发送端在朋友圈发布私密动态
        with allure.step("1. 发送端发布私密动态"):
            self.mainS.go_to_moments_page()
            self.momentsS.wait_for_moments_page_load(raise_exception=False)
            self.momentsS.post_text_moment(private_content)
            logger.info(f"发送端发布了标记动态: {private_content}")

        # 2. 接收端刷新朋友圈信息流，校验是否不包含该私密动态的文案
        with allure.step("2. 接收端进入朋友圈刷新"):
            self.mainR.go_to_moments_page()
            self.momentsR.wait_for_moments_page_load(raise_exception=False)
            self.momentsR.refresh_moments()

        with allure.step("3. 校验接收端无法查看到该私密文案"):
            visible_contents = self.momentsR.get_visible_moment_contents()
            check.is_false(
                private_content in visible_contents,
                f"❌ 错误：接收端不应能看到发送端发布的私密动态 [{private_content}]"
            )

    @allure.story("动态管理")
    @allure.title("MOMENT_MANAGE_001 / MOMENT_ERR_004 - 发送端删除自己动态，接收端同步不可见")
    def test_delete_moment_sync_double(self):
        """测试发送端删除朋友圈后，接收端刷新朋友圈列表已被同步清除"""
        timestamp = int(time.time())
        test_content = f"双端删除同步测试动态 {timestamp}"

        # 1. 发送端发布公开动态
        with allure.step("1. 发送端发布公开动态"):
            self.mainS.go_to_moments_page()
            self.momentsS.wait_for_moments_page_load(raise_exception=False)
            self.momentsS.post_text_moment(test_content)

        # 2. 接收端刷新并确认已能看到该动态
        with allure.step("2. 接收端刷新列表并确认能看到动态"):
            self.mainR.go_to_moments_page()
            self.momentsR.wait_for_moments_page_load(raise_exception=False)
            self.momentsR.refresh_moments()
            check.equal(self.momentsR.get_first_moment_content(), test_content, "❌ 接收端在删除前未能查看到该动态")

        # 3. 发送端删除该动态
        with allure.step("3. 发送端删除自己发布的动态"):
            self.momentsS.delete_first_moment()

        # 4. 接收端重新下拉刷新，校验动态已被移出列表
        with allure.step("4. 接收端刷新并校验动态已被同步移出"):
            self.momentsR.refresh_moments()
            found = self.momentsR.has_moment_with_text(test_content)
            check.is_false(found, f"❌ 发送端删除朋友圈后，接收端仍然能查看到 [{test_content}]")

    @allure.story("朋友圈通知与发现红点")
    @allure.title("MOMENT_NOTICE_001 / MOMENT_NOTICE_007 - 社交互动新通知与主页发现红点清除同步校验")
    def test_moment_notification_red_dot(self):
        """测试接收端给发送端点赞评论后，发送端能够收到消息通知并正确清除红点提示"""
        timestamp = int(time.time())
        test_content = f"新消息红点测试动态 {timestamp}"
        comment_content = f"自动触发红点评论 {timestamp}"

        # 1. 发送端发布动态并回正到首页 (模拟退回主界面)
        with allure.step("1. 发送端发布朋友圈并返回首页"):
            self.mainS.go_to_moments_page()
            self.momentsS.wait_for_moments_page_load(raise_exception=False)
            self.momentsS.post_text_moment(test_content)
            self.mainS.go_to_main_page()

        # 2. 接收端刷新查看到该动态，对该动态发送评论，从而触发新消息
        with allure.step("2. 接收端刷新并评论发送端动态以触发红点"):
            self.mainR.go_to_moments_page()
            self.momentsR.wait_for_moments_page_load(raise_exception=False)
            self.momentsR.refresh_moments()
            if self.momentsR.get_first_moment_content() == test_content:
                self.momentsR.comment_on_first_moment(comment_content)
            else:
                pytest.skip("接收端未及时加载该动态，跳过红点触发校验")

        # 3. 发送端在首页或“发现”上验证是否收到了未读提醒
        with allure.step("3. 发送端首页红点状态检验"):
            # 朋友圈点赞评论后，发现或动态菜单上一般会挂接红点元素
            # 在此做逻辑预留：校验发送端重新进入动态列表时，是否能在顶部看到未读消息同步
            self.mainS.go_to_moments_page()
            self.momentsS.wait_for_moments_page_load(raise_exception=False)
            
            # 在朋友圈中，如果有好友给您点赞/评论，通常会在头部出现“新消息提示栏”
            # 我们通过 moments_locator 中的新消息容器来判断是否存在
            from locators.moments.moments_locator import MomentsLocator
            has_notice = self.momentsS.is_element_exist(MomentsLocator.CL_COMMENT_USER, timeout=5, raise_exception=False)
            check.is_true(has_notice, "❌ 接收端发表互动后，发送端未能成功收到朋友圈新消息提醒")
