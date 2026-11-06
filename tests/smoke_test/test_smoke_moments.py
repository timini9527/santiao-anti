import allure
import pytest
import time
import pytest_check as check
from pages.main.main_page import MainPage
from pages.moments.moments_page import MomentsPage
from pages.home.home_page import HomePage
from pages.common.album_page import CommonAlbumPage
from common.toast_enums import ToastMsg
from core.logger_utils import logger, LogIcon



class BaseSmokeMoments:
    """朋友圈/动态模块测试基类"""

    @pytest.fixture(scope='class', autouse=True)
    def class_setup(self, request, driver_sender):
        """类级别前置与后置：首次确保进入主页并进入朋友圈，类中所有用例执行完毕后统一返回主页"""
        main_page = MainPage(driver_sender)
        home_page = HomePage(driver_sender)
        moments_page = MomentsPage(driver_sender)
        with allure.step('类前置步骤：首次确保进入主页，并进入朋友圈页面'):
            main_page.go_to_main_page()
            home_page.click_bottom_expand_button()
            home_page.click_friend_moments()
        yield
        with allure.step('类后置步骤：所有用例执行完毕，返回首页'):
            try:
                main_page.go_to_main_page()
            except Exception as e:
                logger.error(f'{LogIcon.FAIL} 类级 Teardown 失败，未能返回首页: {e}')

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender):
        """方法级别前置与后置：确保页面对象就绪并在每次执行后清理编辑区残留"""
        self.mainPage = MainPage(driver_sender)
        self.momentsPage = MomentsPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.albumPage = CommonAlbumPage(driver_sender)
        yield
        try:
            if self.momentsPage.is_publish_editor_displayed():
                logger.warning(f'{LogIcon.WARN} 冒烟用例运行结束但残留编辑页，执行强制退出...')
                self.momentsPage.click_iv_back()
                try:
                    self.momentsPage.confirm_delete_moment()
                except Exception:
                    pass
                self.momentsPage.wait_for_moments_page_load()
        except Exception as e:
            logger.error(f'{LogIcon.FAIL} 方法级 Teardown 状态重置失败: {e}')

    def _verify_moment_published(self, expected_content: str, timeout: int = 15) -> bool:
        """通用发布成功校验：等待 Toast，轮询刷新列表，直到最新内容出现在首位"""
        toast = self.momentsPage.get_toast(ToastMsg.MOMENT_PUBLISH_SUCCESS, timeout=timeout)
        check.is_true(toast, '❌ 朋友圈未正常弹出‘发布成功’提示')
        self.momentsPage.wait_for_moments_page_load(timeout=timeout)

        def check_published_on_top():
            self.momentsPage.refresh_moments()
            first_text = self.momentsPage.get_first_moment_content(0)
            return expected_content in first_text

        published = self._wait_until(
            check_published_on_top,
            timeout=timeout,
            interval=1.0,
            description=f"等待最新发布内容 [{expected_content}] 在首位展现"
        )
        check.is_true(published, f'❌ 最新发布的朋友圈正文未在首位展示，预期包含 [{expected_content}]')
        return published

    def _delete_test_moment(self, content: str):
        """防误删删除第一条动态校验（含异步等待与列表重置稳态保障）"""
        try:
            first_content = self.momentsPage.get_first_moment_content(0)
            if content in first_content:
                self.momentsPage.delete_first_moment()
                deleted = self._wait_until(
                    lambda: not self.momentsPage.has_moment_with_text(content),
                    timeout=5,
                    description=f"等待临时动态 [{content}] 彻底删除"
                )
                check.is_true(deleted, f'❌ 临时朋友圈 [{content}] 删除后依然在列表中可见')
                self.momentsPage.refresh_moments()
            else:
                logger.warning(f'{LogIcon.WARN} 列表中首条朋友圈为 [{first_content}]，不匹配期望删除的 [{content}]，跳过删除以防误伤原始数据')
        except Exception as e:
            logger.error(f'{LogIcon.WARN} 删除测试朋友圈异常: {e}')

    def _wait_until(self, condition, timeout: int = 5, interval: float = 0.5, description: str = "") -> bool:
        """轮询等待异步 UI 状态变化，避免固定 sleep 或网络延迟导致的偶发断言失败"""
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
            logger.warning(f"{LogIcon.WARN} 等待条件 [{description}] 期间发生异常: {last_error}")
        return False




@allure.epic('IM核心功能测试')
@allure.feature('冒烟测试-朋友圈与动态')
class TestSmokeMoments(BaseSmokeMoments):
    """朋友圈/动态模块核心冒烟用例集 (闭环与鲁棒性保障)"""

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.smoke
    @allure.story('朋友圈信息流与基础交互')
    @allure.title('朋友圈基础冒烟-进入与刷新信息流-状态：已完成')
    def test_smoke_enter_and_refresh(self):
        """测试进入朋友圈并刷新信息流的基础状态，验证主页加载与下拉刷新稳定性"""
        with allure.step('1. 确认已成功加载朋友圈主页及核心交互入口'):
            is_loaded = self.momentsPage.wait_for_moments_page_load()
            check.is_true(is_loaded, '❌ 进入朋友圈主页加载超时，未检测到动态标题')
            is_camera = self.momentsPage.is_camera_displayed()
            check.is_true(is_camera, '❌ 朋友圈主页右上角发布相机入口未正常渲染')
        with allure.step('2. 执行下拉刷新操作并校验界面恢复正常交互状态'):
            self.momentsPage.refresh_moments()
            check.is_true(self.momentsPage.wait_for_moments_page_load(), '❌ 刷新后朋友圈主页标题加载异常')
            check.is_true(self.momentsPage.is_camera_displayed(), '❌ 刷新后朋友圈核心功能入口丢失或异常')

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @allure.story('动态发布与验证')
    @allure.title('发布纯文本动态并在列表首位成功展示与删除-状态：已完成')
    def test_smoke_post_text_moment(self):
        """测试发布纯文字朋友圈的核心链路 (包含数据闭环清理)"""
        test_content = f'冒烟文字动态_{int(time.time() * 1000)}'
        with allure.step('1. 长按相机按钮进入纯文字编辑页并输入'):
            self.momentsPage.long_press_post_moments(1000)
            check.is_true(self.momentsPage.is_publish_editor_displayed(), '❌ 长按未成功进入动态文字编辑页')
            self.momentsPage.input_moments_content(test_content)
        try:
            with allure.step('2. 点击发表并校验'):
                self.momentsPage.click_publish()
                is_published = self._verify_moment_published(test_content)
                if is_published:
                    check.is_false(self.momentsPage.is_moment_contains_media(motype=1), '❌ 纯文字动态首条不应包含图片媒体')
                    check.is_false(self.momentsPage.is_moment_contains_media(motype=2), '❌ 纯文字动态首条不应包含视频媒体')
        finally:
            with allure.step('3. 后置清理：删除本条临时冒烟动态'):
                self._delete_test_moment(test_content)

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.smoke
    @allure.story('动态发布与验证')
    @allure.title('空内容发布拦截并停留编辑页-状态：已完成')
    def test_smoke_empty_text_moment_blocked(self):
        """测试纯文字发布页空内容不可发表，防止发布校验失效。"""
        with allure.step('1. 长按相机按钮进入纯文字编辑页，不输入任何内容'):
            self.momentsPage.long_press_post_moments(1000)
            check.is_true(self.momentsPage.is_publish_editor_displayed(), '❌ 长按未成功进入动态文字编辑页')
        with allure.step('2. 点击发表，校验空内容拦截提示'):
            self.momentsPage.click_publish()
            toast = self.momentsPage.get_toast('请输入发布内容')
            check.is_true(toast, '❌ 空内容发布未弹出预期拦截提示')
        with allure.step('3. 校验仍停留在发布编辑页，并主动返回朋友圈主页'):
            check.is_true(self.momentsPage.is_publish_editor_displayed(), '❌ 空内容发布后不应退出编辑页')
            self.momentsPage.click_iv_back()
            check.is_true(self.momentsPage.wait_for_moments_page_load(), '❌ 空内容发布拦截后返回朋友圈主页失败')

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @allure.story('动态发布与验证')
    @allure.title('发布单图动态并验证与删除-状态：已完成')
    def test_smoke_post_image_moment(self):
        """测试发布单张图片朋友圈的核心链路 (包含数据闭环清理)"""
        test_content = f'冒烟单图动态_{int(time.time() * 1000)}'
        with allure.step('1. 点击相机并打开相册勾选第1张图片确认'):
            self.momentsPage.click_post_moments()
            self.momentsPage.click_album()
            self.albumPage.click_only_photo_checkbox_by_index(0)
            self.albumPage.click_send_or_complete()
            check.is_true(self.momentsPage.is_publish_editor_displayed(), '❌ 勾选图片确认后未进入发布编辑页')
        try:
            with allure.step('2. 在发布编辑页输入描述并发表'):
                self.momentsPage.input_moments_content(test_content)
                self.momentsPage.click_publish()
                is_published = self._verify_moment_published(test_content)
                if is_published:
                    check.is_true(self.momentsPage.is_moment_contains_media(motype=1), '❌ 朋友圈单图发布后未在首条检测到图片')
        finally:
            with allure.step('3. 后置清理：删除本条临时冒烟图片动态'):
                self._delete_test_moment(test_content)

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @allure.story('动态发布与验证')
    @allure.title('发布单视频动态并验证与删除-状态：已完成')
    def test_smoke_post_video_moment(self):
        """测试发布单个视频朋友圈的核心链路 (包含数据闭环清理)"""
        test_content = f'冒烟视频动态_{int(time.time() * 1000)}'
        with allure.step('1. 点击相机并打开相册勾选第1个视频确认'):
            self.momentsPage.click_post_moments()
            self.momentsPage.click_album()
            self.albumPage.click_only_video_checkbox_by_index(0)
            self.albumPage.click_send_or_complete()
            check.is_true(self.momentsPage.is_publish_editor_displayed(), '❌ 勾选视频确认后未进入发布编辑页')
        try:
            with allure.step('2. 在发布编辑页输入描述并发表'):
                self.momentsPage.input_moments_content(test_content)
                self.momentsPage.click_publish()
                is_published = self._verify_moment_published(test_content)
                if is_published:
                    check.is_true(self.momentsPage.is_moment_contains_media(motype=2), '❌ 朋友圈视频发布后未在首条检测到视频')
        finally:
            with allure.step('3. 后置清理：删除本条临时冒烟视频动态'):
                self._delete_test_moment(test_content)

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.smoke
    @allure.story('动态发布与验证')
    @allure.title('取消发布朋友圈-放弃编辑二次确认-状态：已完成')
    def test_smoke_cancel_post_moment_dialog(self):
        """测试在发布编辑页输入内容后点击返回并确认放弃编辑的流程"""
        with allure.step('1. 进入纯文字编辑页并输入临时内容'):
            self.momentsPage.long_press_post_moments(1000)
            check.is_true(self.momentsPage.is_publish_editor_displayed(), '❌ 长按未成功进入动态文字编辑页')
            self.momentsPage.input_moments_content('冒烟放弃编辑内容')
        with allure.step('2. 点击返回按钮，在弹出的二次确认对话框中选择‘确认放弃’'):
            self.momentsPage.click_iv_back()
            self.momentsPage.confirm_delete_moment()
        with allure.step('3. 验证已成功返回朋友圈信息流且未停留在编辑页'):
            check.is_false(self.momentsPage.is_publish_editor_displayed(), '❌ 确认放弃编辑后依然停留在发布编辑页')
            check.is_true(self.momentsPage.wait_for_moments_page_load(), '❌ 退出编辑后未成功返回朋友圈主页')

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @allure.story('动态点赞与评论')
    @allure.title('点赞并取消点赞-状态：已完成')
    def test_smoke_like_moment(self):
        """测试对朋友圈动态点赞后可再次取消点赞 (包含状态刷新与数据清理)"""
        moment_content = f'点赞冒烟测试_{int(time.time() * 1000)}'
        with allure.step('1. 前置准备：发布一条测试动态'):
            self.momentsPage.long_press_post_moments(1000)
            self.momentsPage.input_moments_content(moment_content)
            self.momentsPage.click_publish()
            self._verify_moment_published(moment_content)
        try:
            with allure.step('2. 获取该动态的初始点赞状态并执行点赞'):
                before_like = self.momentsPage.get_nth_moment_like_users(0)
                check.equal(before_like, [], '❌ 新发布的动态点赞状态应该为空')
                self.momentsPage.click_like_nth_moment(0)
                like_success = self._wait_until(
                    lambda: len(self.momentsPage.get_nth_moment_like_users(0)) > 0,
                    timeout=5,
                    description='点赞后点赞用户列表异步更新'
                )
                check.is_true(like_success, '❌ 点赞后点赞用户列表未在预期时间内更新')
            with allure.step('3. 刷新后校验点赞状态仍保持'):
                self.momentsPage.refresh_moments()
                current_like = self.momentsPage.get_nth_moment_like_users(0)
                check.is_true(len(current_like) > 0, '❌ 刷新后点赞状态未保持')
            with allure.step('4. 执行取消点赞并刷新校验'):
                self.momentsPage.click_like_nth_moment(0)
                cancel_success = self._wait_until(
                    lambda: len(self.momentsPage.get_nth_moment_like_users(0)) == 0,
                    timeout=5,
                    description='取消点赞后点赞列表异步恢复为空'
                )
                check.is_true(cancel_success, '❌ 取消点赞后点赞列表未在预期时间内恢复为空')
                self.momentsPage.refresh_moments()
                final_like = self.momentsPage.get_nth_moment_like_users(0)
                check.equal(final_like, [], '❌ 取消点赞并刷新后，点赞列表未恢复为空')
        finally:
            with allure.step('5. 后置清理：删除用于点赞测试的临时动态'):
                self._delete_test_moment(moment_content)

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @allure.story('动态点赞与评论')
    @allure.title('发表评论并删除评论-状态：已完成')
    def test_smoke_comment_moment(self):
        """测试对朋友圈发表评论后刷新可见，并能成功删除 (包含数据闭环)"""
        moment_content = f'评论冒烟测试_{int(time.time() * 1000)}'
        test_comment = f'冒烟测试评论_{int(time.time() * 1000)}'
        with allure.step('1. 前置准备：发布一条测试动态'):
            self.momentsPage.long_press_post_moments(1000)
            self.momentsPage.input_moments_content(moment_content)
            self.momentsPage.click_publish()
            self._verify_moment_published(moment_content)
        try:
            with allure.step('2. 发表一条测试评论并校验列表展示'):
                self.momentsPage.click_comment_on_nth_moment(0)
                self.momentsPage.post_comment(test_comment)
                comment_appeared = self._wait_until(
                    lambda: any(test_comment in comment for comment in self.momentsPage.get_comment_texts(raise_exception=False)),
                    timeout=5,
                    description='评论列表中呈现新发表的评论'
                )
                check.is_true(comment_appeared, f'❌ 列表中未在预期时间内呈现发表的评论: [{test_comment}]')
            with allure.step('3. 刷新朋友圈校验评论仍存在'):
                self.momentsPage.refresh_moments()
                comments_after_refresh = self.momentsPage.get_comment_texts(raise_exception=False)
                check.is_true(any((test_comment in comment for comment in comments_after_refresh)), f'❌ 刷新后评论不应消失: [{test_comment}]')
            with allure.step('4. 点击并删除该条评论并校验已消失'):
                self.momentsPage.delete_own_comment_with_confirm(test_comment)
                comment_removed = self._wait_until(
                    lambda: not any(test_comment in comment for comment in self.momentsPage.get_comment_texts(raise_exception=False)),
                    timeout=5,
                    description='评论列表中已删除的评论消失'
                )
                check.is_true(comment_removed, f'❌ 评论删除后未在预期时间内从列表中移除: [{test_comment}]')
        finally:
            with allure.step('5. 后置清理：删除用于评论测试的临时动态'):
                self._delete_test_moment(moment_content)