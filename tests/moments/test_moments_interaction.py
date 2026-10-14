import allure
import pytest
import time
import pytest_check as check
from pages.main.main_page import MainPage
from pages.moments.moments_page import MomentsPage
from pages.home.home_page import HomePage
from core.logger_utils import logger
from utils.file_reader.data_loader import load_yaml_data


@allure.epic("IM核心功能测试")
@allure.feature("朋友圈模块-互动")
class TestMomentsInteraction:
    _comment_cases_data = load_yaml_data("moments/moments_data.yaml")["comment_cases"]

    @pytest.fixture(scope="class", autouse=True)
    def class_setup(self, request, driver_sender):
        """类级别前置与后置：进入朋友圈并在类中所有用例执行完毕后返回主页"""
        main_page = MainPage(driver_sender)
        home_page = HomePage(driver_sender)
        
        with allure.step("类前置步骤：进入朋友圈页面"):
            home_page.click_bottom_expand_button()
            home_page.click_dynamic()
            
        yield
        
        with allure.step("类后置步骤：所有用例执行完毕，返回首页"):
            try:
                main_page.go_to_main_page()
            except Exception as e:
                logger.error(f"类级 Teardown 失败，未能返回首页: {e}")

    @pytest.fixture(autouse=True)
    def method_setup(self, driver_sender):
        """方法级别前置与后置：初始化页面对象并在每个用例结束后确保页面状态干净"""
        self.mainPage = MainPage(driver_sender)
        self.momentsPage = MomentsPage(driver_sender)
        self.homePage = HomePage(driver_sender)

        yield

    def _verify_moment_published(self, expected_content: str, timeout: int=10):
        """校验朋友圈发布结果：验证弹出‘发布成功’，且最新发布的动态首条匹配"""
        toast = self.momentsPage.get_toast("发布成功", timeout=timeout)
        check.is_true(toast, "❌ 朋友圈发布动态未能弹出‘发布成功’提示")
        self.momentsPage.wait_for_moments_page_load(timeout=timeout)
        
        self.momentsPage.refresh_moments()
        first_content = self.momentsPage.get_first_moment_content(0)
        check.equal(first_content, expected_content, "❌ 朋友圈列表中最新发布的动态内容不匹配")

    def _publish_test_moment(self, content: str) -> str:
        """发布文本测试朋友圈，返回包含时间戳的实际正文"""
        timestamp = int(time.time())
        actual_content = content + str(timestamp)
        self.momentsPage.post_text_moment(actual_content)
        self._verify_moment_published(actual_content)
        return actual_content

    def _delete_test_moment(self, content: str):
        """删除测试朋友圈 (带防误删校验)"""
        first_content = self.momentsPage.get_first_moment_content(0)
        if content in first_content:
            self.momentsPage.delete_first_moment()
            found = self.momentsPage.has_moment_with_text(content)
            check.is_false(found, f"❌ 测试临时动态 [{content}] 删除后依然可见")
        else:
            logger.warning(f"⚠️ [Teardown] 首条朋友圈内容 [{first_content}] 与要删内容 [{content}] 不匹配，跳过删除以防误删他人数据")

    def _wait_until(self, condition, timeout: int = 5, interval: float = 0.5, description: str = "") -> bool:
        """轮询等待异步 UI 状态，避免固定 sleep 导致慢设备误判"""
        deadline = time.time() + timeout
        last_error = None
        while time.time() < deadline:
            try:
                if condition():
                    return True
            except Exception as e:
                last_error = e
            time.sleep(interval)
        if last_error:
            logger.warning(f"⚠️ 等待条件 [{description}] 期间最后一次异常: {last_error}")
        return False

    def _wait_for_comment_state(self, comment_text: str, should_exist: bool = True, timeout: int = 5) -> bool:
        """等待指定评论出现或消失"""
        def _matched():
            comments = self.momentsPage.get_comment_texts(timeout=1, raise_exception=False)
            exists = any(comment_text in comment for comment in comments)
            return exists if should_exist else not exists

        action = "出现" if should_exist else "消失"
        return self._wait_until(_matched, timeout=timeout, description=f"评论 [{comment_text}] {action}")


    @pytest.fixture
    def temp_interaction_moment(self, request):
        """互动测试通用临时朋友圈，根据测试用例名动态生成内容前缀，保证数据辨识度与闭环"""
        test_name = request.node.name.lower()
        
        if "like" in test_name:
            prefix = "点赞测试动态_"
        elif "empty" in test_name:
            prefix = "空评论测试临时动态_"
        elif "persist" in test_name:
            prefix = "评论持久化动态_"
        elif "cancel" in test_name:
            prefix = "取消删除评论动态_"
        elif "comment" in test_name:
            prefix = "评论测试专用动态_"
        else:
            prefix = "互动测试临时动态_"

        actual_content = self._publish_test_moment(prefix)
        yield actual_content
        with allure.step(f"后置清理：删除{prefix[:-1]}"):
            self._delete_test_moment(actual_content)




    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("点赞与评论")
    @allure.title("点赞并取消点赞-状态：已完成")
    def test_like_and_cancel_moment(self, temp_interaction_moment):
        """测试对朋友圈动态点赞后可再次取消点赞（自产自销，数据闭环）"""
        
        with allure.step("1. 获取该动态的初始点赞状态（预期为空）"):
            before_like = self.momentsPage.get_nth_moment_like_users(0)
            check.equal(before_like, [], "❌ 新发布的动态点赞状态应该为空")

        with allure.step("2. 正常执行点赞"):
            self.momentsPage.click_like_nth_moment(0)
            like_changed = self._wait_until(
                lambda: self.momentsPage.get_nth_moment_like_users(0) != before_like,
                timeout=5,
                description="点赞后点赞列表变化"
            )
            check.is_true(like_changed, "❌ 点赞后点赞状态未在预期时间内变化")
            after_like = self.momentsPage.get_nth_moment_like_users(0)
            check.not_equal(after_like, before_like, "❌ 点赞后点赞状态未发生变化")

        with allure.step("3. 刷新后校验点赞状态仍保持"):
            self.momentsPage.refresh_moments()
            like_persisted = self._wait_until(
                lambda: self.momentsPage.get_nth_moment_like_users(0) == after_like,
                timeout=5,
                description="刷新后点赞状态保持"
            )
            check.is_true(like_persisted, "❌ 刷新后点赞状态未保持")

        with allure.step("4. 正常执行取消点赞"):
            self.momentsPage.click_like_nth_moment(0)
            like_cancelled = self._wait_until(
                lambda: self.momentsPage.get_nth_moment_like_users(0) == before_like,
                timeout=5,
                description="取消点赞后点赞列表恢复"
            )
            check.is_true(like_cancelled, "❌ 取消点赞后状态未在预期时间内恢复")
            after_cancel = self.momentsPage.get_nth_moment_like_users(0)
            check.equal(after_cancel, before_like, "❌ 取消点赞后状态未恢复到点赞前")

        with allure.step("5. 刷新后校验取消点赞状态仍保持"):
            self.momentsPage.refresh_moments()
            cancel_persisted = self._wait_until(
                lambda: self.momentsPage.get_nth_moment_like_users(0) == before_like,
                timeout=5,
                description="刷新后取消点赞状态保持"
            )
            check.is_true(cancel_persisted, "❌ 刷新后取消点赞状态未保持")


    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("点赞与评论")
    @allure.title("评论朋友圈-{case_id}-状态：已完成")
    @pytest.mark.parametrize(
        "case_data",
        _comment_cases_data,
        ids=lambda x: x["desc"]
    )
    def test_comment_moment(self, case_data, temp_interaction_moment):
        """测试对朋友圈动态发表不同内容评论（普通、Emoji、长文本限制、敏感词）"""
        case_id = case_data["id"]
        desc = case_data["desc"]
        comment_text = case_data["input_content"]
        expected_behavior = case_data["expected"]["behavior"]
        expected_toast = case_data["expected"]["toast"]

        if expected_behavior == "truncated":
            comment_text = comment_text + "B" * (1005 - len(comment_text))

        allure.dynamic.title(f"评论朋友圈 - {case_id} - {desc}")

        try:
            with allure.step(f"2. 为该动态发表评论：{desc}"):
                self.momentsPage.click_comment_on_nth_moment(0)
                self.momentsPage.send_comment_text(comment_text)

            with allure.step("3. 校验并发送评论"):
                if expected_behavior == "truncated":
                    limit_toast = self.momentsPage.get_toast(expected_toast)
                    check.is_true(limit_toast, f"❌ {case_id} 超长评论未弹出字数限制提示")

                self.momentsPage.send_comment()

                if expected_behavior == "blocked":
                    blocked_toast = self.momentsPage.get_toast(expected_toast)
                    check.is_true(blocked_toast, f"❌ {case_id} 敏感词评论未被正确拦截")

            if expected_behavior == "success":
                with allure.step("4. 校验评论是否成功展示在列表中"):
                    comment_visible = self._wait_for_comment_state(comment_text, should_exist=True)
                    check.is_true(comment_visible, f"❌ {case_id} 评论未在预期时间内展示: {comment_text}")
                    comments = self.momentsPage.get_comment_texts()
                    check.is_true(
                        any(comment_text in comment for comment in comments),
                        f"❌ {case_id} 未在列表中找到已发表的评论: {comment_text}"
                    )
            elif expected_behavior == "truncated":
                with allure.step("4. 校验超长评论是否被自动截断为 999 字符"):
                    truncated_text = comment_text[:999]
                    comment_visible = self._wait_for_comment_state(truncated_text, should_exist=True)
                    check.is_true(comment_visible, f"❌ {case_id} 截断评论未在预期时间内展示")
                    comments = self.momentsPage.get_comment_texts()
                    
                    matched_comment = next((c for c in comments if truncated_text in c), "")
                    check.is_true(bool(matched_comment), f"❌ {case_id} 未在列表中找到截断后的 999 字符评论")
                    
                    if matched_comment:
                        content_part = matched_comment.split(":", 1)[-1].strip()
                        content_part = content_part.split("：", 1)[-1].strip()
                        check.equal(len(content_part), 999, f"❌ {case_id} 评论长度未被截断为 999 字符")

            elif expected_behavior == "blocked":
                with allure.step("4. 校验敏感词评论未展示在列表中"):
                    comment_blocked = self._wait_for_comment_state(comment_text, should_exist=False)
                    check.is_true(comment_blocked, f"❌ {case_id} 敏感词评论应保持不可见")
                    comments = self.momentsPage.get_comment_texts()
                    check.is_false(
                        any(comment_text in comment for comment in comments),
                        f"❌ {case_id} 敏感词评论不应展示在列表中"
                    )

        finally:
            with allure.step("5. 后置清理：清理评论框与本用例所发评论"):
                if expected_behavior == "success":
                    try:
                        self.momentsPage.delete_own_comment_with_confirm(comment_text)
                    except Exception as e:
                        logger.warning(f"⚠️ 清理本条评论失败: {e}")
                elif expected_behavior == "truncated":
                    try:
                        self.momentsPage.delete_own_comment_with_confirm(comment_text[:999])
                    except Exception as e:
                        logger.warning(f"⚠️ 清理本条截断评论失败: {e}")


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story("点赞与评论")
    @allure.title("评论为空不可发送-状态：已完成")
    def test_empty_comment_cannot_send(self, temp_interaction_moment):
        """测试空评论不能成功发送"""
        with allure.step("1. 获取发送空评论前的评论列表"):
            before_comments = self.momentsPage.get_comment_texts(2, False)

        with allure.step("2. 点击评论按钮并不输入内容尝试点击发送"):
            self.momentsPage.click_comment_on_nth_moment(0)
            self.momentsPage.send_comment()

        with allure.step("3. 校验评论列表未新增空评论且未成功发送"):
            after_comments = self.momentsPage.get_comment_texts(2, False)
            check.equal(after_comments, before_comments, "❌ 空评论不应被成功发送，评论列表应当保持不变")


    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("点赞与评论")
    @allure.title("评论成功后刷新仍可见-状态：已完成")
    def test_comment_persists_after_refresh(self, temp_interaction_moment):
        """测试评论成功后刷新朋友圈，评论仍然可见"""
        timestamp = int(time.time())
        test_comment = f"刷新持久化评论 {timestamp}"

        try:
            with allure.step("1. 发表一条测试评论"):
                self.momentsPage.click_comment_on_nth_moment(0)
                self.momentsPage.post_comment(test_comment)
                comment_visible = self._wait_for_comment_state(test_comment, should_exist=True)
                check.is_true(comment_visible, f"❌ 评论未成功展示: {test_comment}")

            with allure.step("2. 刷新朋友圈并校验评论仍存在"):
                self.momentsPage.refresh_moments()
                comment_persisted = self._wait_for_comment_state(test_comment, should_exist=True)
                check.is_true(comment_persisted, f"❌ 刷新后评论未保持可见: {test_comment}")
        finally:
            with allure.step("3. 后置清理：删除刷新持久化测试评论"):
                try:
                    self.momentsPage.delete_own_comment_with_confirm(test_comment)
                except Exception as e:
                    logger.warning(f"⚠️ 清理刷新持久化测试评论失败: {e}")


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story("点赞与评论")
    @allure.title("取消删除自己的评论-状态：已完成")
    def test_cancel_delete_own_comment(self, temp_interaction_moment):
        """测试点击删除自己的评论后取消，评论仍然保留"""
        timestamp = int(time.time())
        test_comment = f"取消删除评论 {timestamp}"

        try:
            with allure.step("1. 发表一条测试评论"):
                self.momentsPage.click_comment_on_nth_moment(0)
                self.momentsPage.post_comment(test_comment)
                comment_visible = self._wait_for_comment_state(test_comment, should_exist=True)
                check.is_true(comment_visible, f"❌ 评论未成功展示: {test_comment}")

            with allure.step("2. 点击评论触发删除弹窗后选择取消"):
                self.momentsPage.delete_own_comment(test_comment)
                self.momentsPage.cancel_delete_comment()

            with allure.step("3. 校验取消删除后评论仍然存在"):
                comment_still_visible = self._wait_for_comment_state(test_comment, should_exist=True)
                check.is_true(comment_still_visible, f"❌ 取消删除后评论不应消失: {test_comment}")
        finally:
            with allure.step("4. 后置清理：删除取消删除测试评论"):
                try:
                    self.momentsPage.delete_own_comment_with_confirm(test_comment)
                except Exception as e:
                    logger.warning(f"⚠️ 清理取消删除测试评论失败: {e}")



    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("点赞与评论")
    @allure.title("删除自己的评论-状态：已完成")
    def test_delete_own_comment(self, temp_interaction_moment):
        """测试自己发表的评论可以被点击并成功删除 (数据闭环)"""
        timestamp = int(time.time())
        test_comment = f"待删除的自发评论 {timestamp}"

        with allure.step("1. 发表一条新评论"):
            self.momentsPage.click_comment_on_nth_moment(0)
            self.momentsPage.post_comment(test_comment)

        with allure.step("2. 确认评论列表中出现了该条评论"):
            comment_visible = self._wait_for_comment_state(test_comment, should_exist=True)
            check.is_true(comment_visible, f"❌ 未在预期时间内看到待删除评论: {test_comment}")
            comments = self.momentsPage.get_comment_texts(raise_exception=False)
            check.is_true(
                any(test_comment in comment for comment in comments),
                f"❌ 未成功发表待删除评论: {test_comment}"
            )

        with allure.step("3. 点击该条评论，触发删除并二次确认"):
            self.momentsPage.delete_own_comment_with_confirm(test_comment)

        with allure.step("4. 校验该评论已从列表中消失"):
            comment_deleted = self._wait_for_comment_state(test_comment, should_exist=False)
            check.is_true(comment_deleted, f"❌ 评论 [{test_comment}] 删除后仍在预期时间内可见")
            comments_after = self.momentsPage.get_comment_texts(raise_exception=False)
            check.is_false(
                any(test_comment in comment for comment in comments_after),
                f"❌ 评论 [{test_comment}] 删除后依然可见"
            )



    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("点赞与评论")
    @allure.title("点赞并取消点赞-状态：已完成")
    def test_like_and_cancel_moment(self, temp_like_moment):
        """测试对朋友圈动态点赞后可再次取消点赞（自产自销，数据闭环）"""
        
        with allure.step("1. 获取该动态的初始点赞状态（预期为空）"):
            before_like = self.momentsPage.get_nth_moment_like_users(0)
            check.equal(before_like, [], "❌ 新发布的动态点赞状态应该为空")

        with allure.step("2. 正常执行点赞"):
            self.momentsPage.click_like_nth_moment(0)
            like_changed = self._wait_until(
                lambda: self.momentsPage.get_nth_moment_like_users(0) != before_like,
                timeout=5,
                description="点赞后点赞列表变化"
            )
            check.is_true(like_changed, "❌ 点赞后点赞状态未在预期时间内变化")
            after_like = self.momentsPage.get_nth_moment_like_users(0)
            check.not_equal(after_like, before_like, "❌ 点赞后点赞状态未发生变化")

        with allure.step("3. 刷新后校验点赞状态仍保持"):
            self.momentsPage.refresh_moments()
            like_persisted = self._wait_until(
                lambda: self.momentsPage.get_nth_moment_like_users(0) == after_like,
                timeout=5,
                description="刷新后点赞状态保持"
            )
            check.is_true(like_persisted, "❌ 刷新后点赞状态未保持")

        with allure.step("4. 正常执行取消点赞"):
            self.momentsPage.click_like_nth_moment(0)
            like_cancelled = self._wait_until(
                lambda: self.momentsPage.get_nth_moment_like_users(0) == before_like,
                timeout=5,
                description="取消点赞后点赞列表恢复"
            )
            check.is_true(like_cancelled, "❌ 取消点赞后状态未在预期时间内恢复")
            after_cancel = self.momentsPage.get_nth_moment_like_users(0)
            check.equal(after_cancel, before_like, "❌ 取消点赞后状态未恢复到点赞前")

        with allure.step("5. 刷新后校验取消点赞状态仍保持"):
            self.momentsPage.refresh_moments()
            cancel_persisted = self._wait_until(
                lambda: self.momentsPage.get_nth_moment_like_users(0) == before_like,
                timeout=5,
                description="刷新后取消点赞状态保持"
            )
            check.is_true(cancel_persisted, "❌ 刷新后取消点赞状态未保持")



