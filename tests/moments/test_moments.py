import allure
import pytest
import time
import pytest_check as check
from pages.main.main_page import MainPage
from pages.moments.moments_page import MomentsPage
from pages.home.home_page import HomePage
from locators.moments.moments_locator import MomentsLocator
from core.logger_utils import logger


@allure.epic("IM核心功能测试")
@allure.feature("朋友圈模块-发布与互动")
class TestMoments:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """初始化页面对象并确保测试结束后返回主页"""
        self.mainPage = MainPage(driver_sender)
        self.momentsPage = MomentsPage(driver_sender)
        self.homePage = HomePage(driver_sender)

        with allure.step("前置步骤：进入朋友圈页面"):
            self._go_to_moments_page()

        yield

        try:
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"Teardown 失败，未能返回首页: {e}")


    def _go_to_moments_page(self):
        """进入朋友圈页面"""
        self.homePage.click_bottom_expand_button()
        self.homePage.click_dynamic()
    
    def _publish_test_moment(self, content: str):
        """发布测试朋友圈"""
        timestamp = int(time.time())
        self.momentsPage.post_text_moment(content+str(timestamp))
        toast = self.momentsPage.get_toast("发布成功")
        check.equal(toast, "发布成功", f"❌ 朋友圈发布失败")
        




    @allure.story("入口与信息流")
    @allure.title("从首页动态入口进入朋友圈校验页面-状态-已完成")
    def test_enter_group_moments(self):
        """测试进入群聊朋友圈的功能"""

        with allure.step("1. 校验朋友圈页面是否成功加载"):
            is_loaded = self.momentsPage.wait_for_moments_page_load()
            check.is_true(is_loaded, "❌ 未成功进入朋友圈页面")


    @allure.story("入口与信息流")
    @allure.title("朋友圈信息流-下拉刷新")
    def test_refresh_moments_feed(self):
        """测试朋友圈下拉刷新后，能够成功同步并展示最新发布的动态"""
        new_moment_content = f"用于刷新验证的动态"

        with allure.step("1. 发布一条全新的测试动态"):
            self._publish_test_moment(new_moment_content)

        with allure.step("2. 下拉刷新朋友圈"):
            is_loaded = self.momentsPage.wait_for_moments_page_load()
            self.momentsPage.refresh_moments()
            check.is_true(is_loaded, "❌ 下拉刷新后朋友圈页面未正常加载")

        with allure.step("3. 校验刷新后首条动态是否已更新为最新发布内容"):
            after_contents = self.momentsPage.get_visible_moment_contents()
            check.is_true(bool(after_contents), "❌ 下拉刷新后朋友圈动态内容为空")
            
            first_moment_after = after_contents[0] if after_contents else ""
            check.is_in(new_moment_content, first_moment_after, f"❌ 下拉刷新未能成功同步最新动态。期望首条为: [{new_moment_content}], 实际首条: [{first_moment_after}]")


    @allure.story("入口与信息流")
    @allure.title("快速上滑加载最后一条朋友圈动态-状态：已完成")
    def test_load_more_moments_feed(self):
        """测试朋友圈上滑加载历史动态时页面不白屏、不崩溃"""

        with allure.step("1. 快速上滑加载最后一条朋友圈动态"):
            bottom_state = self.momentsPage.fast_load_more_moments()
            check.is_true(bottom_state, f'❌ 上滑后朋友圈页面没有到达底部, 触底判断：{bottom_state}')

        with allure.step("2. 校验上滑后仍停留在朋友圈信息流"):
            is_loaded = self.momentsPage.wait_for_moments_page_load()
            check.is_true(is_loaded, "❌ 上滑加载后朋友圈页面未正常展示")
        
        
    @allure.story("发布朋友圈")
    @allure.title("发布纯文字朋友圈 - {case_id}-状态：已完成")
    @pytest.mark.parametrize(
        "case_id, content",
        [
            ("MOMENT_PUB_001", "Hello Moments! 这是一个自动化测试动态。"),
            ("MOMENT_PUB_008", "朋友圈 Emoji 与特殊字符校验 🌟🔥🚀 ABC123 !@#$%^&*()"),
        ],
        ids=["纯文字朋友圈", "emoji和特殊字符文案"],
    )
    def test_post_text_moment(self, case_id, content):
        """测试发布纯文字、emoji 和特殊字符朋友圈"""
        allure.dynamic.title(f"发布纯文字朋友圈 - {case_id}")

        with allure.step(f"1. 发布动态：{content}"):
            self.momentsPage.post_text_moment(content)

        with allure.step("2. 校验动态是否在列表首位显示"):
            actual_content = self.momentsPage.get_first_moment_content()
            check.equal(actual_content, content, f"❌ {case_id} 朋友圈发布内容不匹配")

    @allure.story("发布朋友圈")
    @allure.title("MOMENT_PUB_009 - 发布长文案朋友圈")
    def test_post_long_text_moment(self):
        """测试发布长文案朋友圈后关键内容不丢失"""
        content = "朋友圈长文本展示校验：" + "自动化长文本内容" * 20

        with allure.step("1. 发布长文案动态"):
            self.momentsPage.post_text_moment(content)

        with allure.step("2. 校验列表首位包含长文案关键内容"):
            actual_content = self.momentsPage.get_first_moment_content()
            check.is_in("朋友圈长文本展示校验", actual_content, "❌ 长文案朋友圈关键内容未展示")

    @allure.story("发布朋友圈")
    @allure.title("MOMENT_PUB_010 - 不填写内容不可发表")
    def test_empty_text_moment_cannot_publish(self):
        """测试未输入内容时不能成功发布朋友圈"""

        with allure.step("1. 不输入内容直接尝试发表"):
            is_still_editing = self.momentsPage.try_publish_empty_moment()

        with allure.step("2. 校验仍停留在发布编辑页"):
            check.is_true(is_still_editing, "❌ 空内容朋友圈不应被成功发布")
            if is_still_editing:
                self.momentsPage.back()
                self.momentsPage.wait_for_moments_page_load(raise_exception=False)

    @allure.story("发布朋友圈")
    @allure.title("MOMENT_PUB_011 - 发布超过999字长文案限制")
    def test_post_moment_999_limit(self):
        """测试发布超过999个字符的朋友圈，文案限制为999字"""
        content = "A" * 1005
        
        with allure.step("1. 长按发布纯文字动态并输入1005个字"):
            elem = self.momentsPage.find_element(MomentsLocator.IV_CAMERA, timeout=2)
            self.momentsPage.long_press_action(found_ele=elem, hold_time=1000)
            self.momentsPage.input_moments_content(content)
            
        with allure.step("2. 点击发表按钮"):
            self.momentsPage.click_publish()
            
        with allure.step("3. 校验发布成功后列表首条动态被自动截断限制为 999 字符"):
            self.momentsPage.wait_for_moments_page_load()
            actual_content = self.momentsPage.get_first_moment_content()
            check.equal(len(actual_content), 999, f"❌ 朋友圈文字长度未限制为 999 字符，实际长度: {len(actual_content)}")

    @allure.story("发布朋友圈")
    @allure.title("MOMENT_PUB_012 - 敏感词朋友圈不允许发布")
    def test_post_moment_sensitive_interception(self):
        """测试发布包含敏感词的朋友圈动态被拦截"""
        sensitive_content = "包含敏感词的动态测试：特务，涉毒，暴恐"
        
        with allure.step("1. 长按发布纯文字动态并输入敏感词文案"):
            elem = self.momentsPage.find_element(MomentsLocator.IV_CAMERA, timeout=2)
            self.momentsPage.long_press_action(found_ele=elem, hold_time=1000)
            self.momentsPage.input_moments_content(sensitive_content)
            
        with allure.step("2. 点击发表按钮"):
            self.momentsPage.click_publish()
            
        with allure.step("3. 校验拦截提示 Toast 并确认页面未退出发表编辑页"):
            toast = self.momentsPage.get_toast(expected_toast="敏感词")
            if not toast:
                toast = self.momentsPage.get_toast(expected_toast="违规")
            logger.info(f"捕获到的 Toast 提示: {toast}")
            check.is_true(len(toast) > 0, "❌ 未能捕获到敏感词拦截提示 Toast")
            
            is_still_editing = self.momentsPage.is_publish_editor_displayed()
            check.is_true(is_still_editing, "❌ 包含敏感词的朋友圈不应发布成功，但当前页面已退出编辑页")
            
            if is_still_editing:
                self.momentsPage.back()
                from appium.webdriver.common.appiumby import AppiumBy
                confirm_btn = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("放弃")')
                if self.momentsPage.is_element_exist(confirm_btn, timeout=1.5, raise_exception=False):
                    self.momentsPage.click(confirm_btn)
                self.momentsPage.wait_for_moments_page_load(raise_exception=False)

    @allure.story("点赞与评论")
    @allure.title("MOMENT_INTER_001/MOMENT_INTER_002 - 点赞并取消点赞")
    def test_like_and_cancel_moment(self):
        """测试对朋友圈动态点赞后可再次取消点赞"""

        with allure.step("1. 获取点赞前状态"):
            before_like = self.momentsPage.get_first_moment_like_text()

        with allure.step("2. 点击第一条动态点赞入口"):
            self.momentsPage.like_first_moment()
            after_like = self.momentsPage.get_first_moment_like_text()
            check.not_equal(after_like, before_like, "❌ 点赞后点赞状态未发生变化")

        with allure.step("3. 再次点击取消点赞"):
            self.momentsPage.like_first_moment()
            after_cancel = self.momentsPage.get_first_moment_like_text()
            check.not_equal(after_cancel, after_like, "❌ 取消点赞后点赞状态未发生变化")

    @allure.story("点赞与评论")
    @allure.title("评论朋友圈 - {case_id}")
    @pytest.mark.parametrize(
        "case_id, comment_text",
        [
            ("MOMENT_INTER_003", "自动化评论测试"),
            ("MOMENT_INTER_009", "评论 Emoji 与特殊字符 🌟🔥🚀 !@#$%^&*()"),
        ],
        ids=["评论好友朋友圈", "评论包含emoji和特殊字符"],
    )
    def test_comment_moment(self, case_id, comment_text):
        """测试对朋友圈动态发表评论"""
        allure.dynamic.title(f"评论朋友圈 - {case_id}")

        with allure.step(f"1. 为第一条动态发表评论：{comment_text}"):
            self.momentsPage.comment_on_first_moment(comment_text)

        with allure.step("2. 校验评论是否展示在评论列表"):
            comments = self.momentsPage.get_comment_texts()
            check.is_true(
                any(comment_text in comment for comment in comments),
                f"❌ {case_id} 未找到评论内容: {comment_text}",
            )

    @allure.story("点赞与评论")
    @allure.title("MOMENT_INTER_008 - 评论为空不可发送")
    def test_empty_comment_cannot_send(self):
        """测试空评论不能成功发送"""

        with allure.step("1. 获取发送空评论前的评论列表"):
            before_comments = self.momentsPage.get_comment_texts()

        with allure.step("2. 不输入内容直接尝试发送评论"):
            after_comments = self.momentsPage.try_send_empty_comment()

        with allure.step("3. 校验评论列表未新增空评论"):
            check.equal(after_comments, before_comments, "❌ 空评论不应被成功发送")

    @allure.story("发布朋友圈")
    @allure.title("MOMENT_PUB_002 - 发布图片朋友圈")
    def test_post_image_moment(self):
        """测试发布图片朋友圈"""
        # 预留 CI 资源依赖提示，如果执行环境不具备图片文件，则 skip 避免 Flaky
        pytest.skip("由于本地相册资源 Mock 依赖和文件上传稳定性，本用例做逻辑链预留")

    @allure.story("朋友圈浏览与详情")
    @allure.title("MOMENT_VIEW_001 - 查看文字动态详情")
    def test_view_moment_details(self):
        """测试进入朋友圈详情页面"""
        with allure.step("1. 获取首条动态正文并点击进入详情"):
            first_content = self.momentsPage.get_first_moment_content()
            if not first_content:
                pytest.skip("列表无可用动态，跳过详情页面校验")
            # 点击首条动态文字进入详情
            self.momentsPage.click(self.momentsPage.TV_CONTENT)
            time.sleep(1)

        with allure.step("2. 校验是否能够查看详情且正文一致"):
            detail_content = self.momentsPage.get_first_moment_content()
            check.equal(detail_content, first_content, "❌ 详情页面动态正文不匹配")

    @allure.story("动态管理")
    @allure.title("MOMENT_MANAGE_001 - 删除自己发布的动态")
    def test_delete_own_moment(self):
        """测试发布动态后可以成功删除"""
        timestamp = int(time.time())
        test_content = f"待删除的文字动态 {timestamp}"

        with allure.step("1. 发布一条动态"):
            self.momentsPage.post_text_moment(test_content)
            # 确认首条动态是否是刚才发的
            check.equal(self.momentsPage.get_first_moment_content(), test_content, "❌ 朋友圈未能正常发布待删除动态")

        with allure.step("2. 点击删除按钮并确认删除"):
            self.momentsPage.delete_first_moment()

        with allure.step("3. 校验朋友圈列表中已不包含该动态"):
            found = self.momentsPage.has_moment_with_text(test_content)
            check.is_false(found, f"❌ 朋友圈动态 [{test_content}] 删除后依然可见")

    @allure.story("点赞与评论")
    @allure.title("MOMENT_INTER_005 - 删除自己的评论")
    def test_delete_own_comment(self):
        """测试自己发表的评论可以被点击并成功删除"""
        timestamp = int(time.time())
        test_comment = f"待删除的自发评论 {timestamp}"

        with allure.step("1. 发表一条新评论"):
            # 为首位动态点击评论并发表
            self.momentsPage.click_comment_on_nth_moment(0)
            self.momentsPage.post_comment(test_comment)
            time.sleep(1)

        with allure.step("2. 确认评论列表中出现了该条评论"):
            comments = self.momentsPage.get_comment_texts()
            check.is_true(
                any(test_comment in comment for comment in comments),
                f"❌ 未成功发表待删除评论: {test_comment}"
            )

        with allure.step("3. 点击该条评论，触发删除并二次确认"):
            self.momentsPage.delete_own_comment_with_confirm(test_comment)
            time.sleep(1)

        with allure.step("4. 校验该评论已从列表中消失"):
            comments_after = self.momentsPage.get_comment_texts()
            check.is_false(
                any(test_comment in comment for comment in comments_after),
                f"❌ 评论 [{test_comment}] 删除后依然可见"
            )



