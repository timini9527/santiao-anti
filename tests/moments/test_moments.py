import allure
import pytest
import time
import pytest_check as check
from pages.main.main_page import MainPage
from pages.moments.moments_page import MomentsPage
from pages.home.home_page import HomePage
from pages.common.album_page import CommonAlbumPage
from core.logger_utils import logger, LogIcon
from utils.file_reader.data_loader import load_yaml_data


@allure.epic("IM核心功能测试")
@allure.feature("朋友圈模块-发布与互动")
class TestMoments:
    _publish_cases_data = load_yaml_data("moments/moments_data.yaml")["test_cases"]

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
                logger.error(f"{LogIcon.FAIL} 类级 Teardown 失败，未能返回首页: {e}")

    @pytest.fixture(autouse=True)
    def method_setup(self, driver_sender):
        """方法级别前置与后置：初始化页面对象并在每个用例结束后确保页面状态干净"""
        self.mainPage = MainPage(driver_sender)
        self.momentsPage = MomentsPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.albumPage = CommonAlbumPage(driver_sender)

        yield

        try:
            if self.momentsPage.is_publish_editor_displayed():
                logger.warning(f"{LogIcon.WARN} 用例执行结束，但仍留在发布编辑页，强行执行返回及清理...")
                self.momentsPage.click_iv_back()
                try:
                    self.momentsPage.confirm_delete_moment()
                except Exception:
                    pass
                self.momentsPage.wait_for_moments_page_load()
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} 方法级 Teardown 恢复朋友圈状态失败: {e}")
    
    
    def _verify_moment_published(self, expected_content: str, timeout: int=10):
        """校验朋友圈发布结果：验证弹出‘发布成功’，且最新发布的动态首条匹配"""
        toast = self.momentsPage.get_toast("发布成功", timeout=timeout)
        check.is_true(toast, "❌ 朋友圈发布动态未能弹出‘发布成功’提示")
        self.momentsPage.wait_for_moments_page_load(timeout=timeout)
        
        # TODO: Android端有BUG，每次点击发布后必须下拉刷新才能看到最新发布
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
        
    def _select_photos_and_confirm(self, count: int, start_index: int = 0, comstate: bool = True):
        """在相册中批量勾选指定数量的纯图片并确认发送"""
        for i in range(start_index, start_index + count):
            self.albumPage.click_only_photo_checkbox_by_index(i)
        
        if comstate:
            self.albumPage.click_send_or_complete()

    def _publish_media_moment(self, actual_content: str):
        """在朋友圈编辑页输入文字描述并发表，同时验证发布成功"""
        with allure.step("发表动态：在朋友圈编辑页输入文字描述并发表"):
            self.momentsPage.input_moments_content(actual_content)
            self.momentsPage.click_publish()
                
        with allure.step("校验结果：验证弹出‘发布成功’，且最新发布的动态首条匹配"):
            self._verify_moment_published(expected_content=actual_content, timeout=60)


    def _delete_test_moment(self, content: str):
        """删除测试朋友圈 (带防误删校验)"""
        first_content = self.momentsPage.get_first_moment_content(0)
        if content in first_content:
            self.momentsPage.delete_first_moment()
            found = self.momentsPage.has_moment_with_text(content)
            check.is_false(found, f"❌ 测试临时动态 [{content}] 删除后依然可见")
        else:
            logger.warning(f"{LogIcon.WARN} 首条朋友圈内容 [{first_content}] 与要删内容 [{content}] 不匹配，跳过删除以防误删他人数据")
            




    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story("入口与信息流")
    @allure.title("从首页动态入口进入朋友圈校验页面-状态-已完成")
    def test_enter_group_moments(self):
        """测试进入群聊朋友圈的功能"""

        with allure.step("1. 校验朋友圈页面是否成功加载"):
            is_loaded = self.momentsPage.wait_for_moments_page_load()
            check.is_true(is_loaded, "❌ 未成功进入朋友圈页面")


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story("入口与信息流")
    @allure.title("朋友圈信息流-下拉刷新-状态：已完成")
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


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
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
        
        
    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("发布朋友圈")
    @allure.title("发布纯文字朋友圈-状态：已完成")
    @pytest.mark.parametrize(
        "case_data",
        _publish_cases_data,
        ids=lambda x: x["desc"]
    )
    def test_post_text_moment(self, case_data):
        """测试发布不同文字内容的朋友圈（普通、Emoji、长文本、超长限制、敏感词）"""
        case_id = case_data["id"]
        desc = case_data["desc"]
        content = case_data["input_content"]
        expected_behavior = case_data["expected"]["behavior"]
        is_expand = case_data["expected"]["is_expand"]
        expected_toast = case_data["expected"]["toast"]

        if expected_behavior == "truncated":
            content = content + "A" * (1005 - len(content))

        allure.dynamic.title(f"发布纯文字朋友圈 - {case_id} - {desc}")

        with allure.step(f"1. 尝试发布动态内容"):
            self.momentsPage.long_press_post_moments(1000)
            self.momentsPage.input_moments_content(content)
        
        with allure.step("2. 校验发布按钮与 Toast 提示并发表"):
            if expected_behavior == "truncated":
                limit_toast = self.momentsPage.get_toast()
                check.equal(expected_toast, limit_toast, f"❌ {case_id} 超出字数限制，朋友圈发布失败")
            
            self.momentsPage.click_publish()
            
            if expected_behavior == "empty":
                empty_toast = self.momentsPage.get_toast(expected_toast)
                check.is_true(empty_toast, f"❌ {case_id} 空内容，朋友圈发布失败")
            elif expected_behavior == "blocked":
                blocked_toast = self.momentsPage.get_toast(expected_toast)
                check.is_true(blocked_toast, f"❌ {case_id} 敏感词，朋友圈发布失败")
            else:
                toast = self.momentsPage.get_toast("发布成功")
                check.is_true(toast, f"❌ {case_id} 正常发布朋友圈失败")
                self.momentsPage.wait_for_moments_page_load()
                # TODO: Android端有BUG，每次点击发布后必须下拉刷新才能看到最新发布
                self.momentsPage.refresh_moments()
            
        if expected_behavior in ["success", "truncated"]:
            with allure.step("3. 校验发布成功后是否停留在朋友圈页面"):
                self.momentsPage.click_expand_or_shrink_moment(is_expand=is_expand)

        if expected_behavior == "success":
            with allure.step("4. 校验动态是否完整显示在列表首位 (且不包含图片与视频)"):
                actual_content = self.momentsPage.get_first_moment_content(0)
                check.equal(actual_content, content, f"❌ {case_id} 正常发布朋友圈内容不匹配")
                check.is_false(self.momentsPage.is_moment_contains_media(motype=1), f"❌ {case_id} 纯文字动态不应包含图片资源")
                check.is_false(self.momentsPage.is_moment_contains_media(motype=2), f"❌ {case_id} 纯文字动态不应包含视频资源")

        elif expected_behavior == "empty":
            with allure.step("4. 校验仍停留在发布编辑页"):
                is_still_editing = self.momentsPage.is_publish_editor_displayed()
                check.is_true(is_still_editing, "❌ 空内容朋友圈不应被成功发布")
                if is_still_editing:
                    self.momentsPage.click_iv_back()
                    self.momentsPage.wait_for_moments_page_load()

        elif expected_behavior == "truncated":
            with allure.step("4. 校验发布成功后列表首条动态被自动截断限制为 999 字符"):
                actual_content = self.momentsPage.get_first_moment_content(0)
                check.equal(len(actual_content), 999, f"❌ {case_id} 朋友圈文字长度未限制为 999 字符")
                check.equal(actual_content, content[:999], f"❌ {case_id} 截断后的朋友圈内容不匹配")

        elif expected_behavior == "blocked":
            with allure.step("4. 校验拦截提示 Toast 并确认页面未退出发表编辑页"):
                is_still_editing = self.momentsPage.is_publish_editor_displayed()
                check.is_true(is_still_editing, "❌ 包含敏感词的朋友圈不应发布成功，但当前页面已退出编辑页")
                
                if is_still_editing:
                    self.momentsPage.click_iv_back()
                    self.momentsPage.confirm_delete_moment()
                    self.momentsPage.wait_for_moments_page_load()


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story("发布朋友圈")
    @allure.title("取消发布朋友圈-二次确认弹窗校验-状态：已完成")
    def test_cancel_post_moment_dialog_validation(self):
        """测试在朋友圈发布编辑页输入内容后，点击返回时的二次确认弹窗逻辑 (包含取消放弃和确认放弃)"""
        with allure.step("1. 点击右上角相机长按进入纯文字编辑页"):
            self.momentsPage.long_press_post_moments(1000)
            self.momentsPage.input_moments_content("测试放弃编辑内容")

        with allure.step("2. 点击返回按钮，并选择“确认放弃”退出编辑"):
            self.momentsPage.click_iv_back()
            self.momentsPage.confirm_delete_moment()
            check.is_false(self.momentsPage.is_publish_editor_displayed(), "❌ 点击“确认”放弃后，应该已经退出朋友圈编辑页")
            check.is_true(self.momentsPage.wait_for_moments_page_load(), "❌ 退出编辑页后应返回朋友圈列表页面")


    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("发布朋友圈")
    @allure.title("朋友圈图片发布-状态：已完成")
    @pytest.mark.parametrize(
        "case_id, title, init_photo_count, add_photo_count, expected_behavior",
        [
            pytest.param("MOMENT_PUB_001", "发布单张图片朋友圈", 1, 0, "success", id="发布单张图片朋友圈"),
            pytest.param("MOMENT_PUB_002", "发布9张图片朋友圈", 9, 0, "success", id="发布9张图片朋友圈"),
            pytest.param("MOMENT_PUB_003", "选择图片超过上限9张拦截提示", 10, 0, "overlimit_toast", id="选择图片超过上限9张拦截提示"),
            pytest.param("MOMENT_PUB_004", "已选择图片少于9张时继续添加", 3, 2, "add_more_and_publish", id="已选择图片少于9张时继续添加"),
        ],
    )
    def test_post_image_moment_scenarios(self, request, case_id, title, init_photo_count, add_photo_count, expected_behavior):
        """测试多图发布朋友圈的各种场景 (包含单图发布、超限拦截和追加图片)"""
        allure.dynamic.title(f"{case_id} - {title}")
        
        test_text = f"图片测试_{title}_{case_id}_"
        actual_content = f"{test_text}{int(time.time())}"
        
        with allure.step("1. 点击右上角相机按钮并选择从相册选择"):
            self.momentsPage.click_post_moments()
            self.momentsPage.click_album()
            
        if expected_behavior == "success":
            with allure.step(f"2. 勾选前 {init_photo_count} 张图片并点击发送/完成"):
                self._select_photos_and_confirm(count=init_photo_count)
                
        elif expected_behavior == "overlimit_toast":
            with allure.step("2. 选择 10 张图片并验证超限拦截提示"):
                self._select_photos_and_confirm(count=init_photo_count, comstate=False)
                has_dialog, msg = self.albumPage.handle_overlimit_dialog()
                check.is_true(has_dialog, f"❌ {case_id} 勾选第 10 张时未检测到超限警告弹窗")
                check.is_in("你最多只能选择9张照片", msg, f"❌ {case_id} 超限警告提示不符合预期: {msg}")
                self.albumPage.click_send_or_complete()
                    
        elif expected_behavior == "add_more_and_publish":
            with allure.step(f"2. 首次勾选 {init_photo_count} 张图片并返回编辑页"):
                self._select_photos_and_confirm(count=init_photo_count)
                
            with allure.step(f"3. 校验当前编辑页已选图片为 {init_photo_count} 张，并点击加号继续添加"):
                current_count = self.momentsPage.get_selected_photo_count()
                check.equal(current_count, init_photo_count, f"❌ 编辑页初始展示图片数量与预期不符")
                self.momentsPage.click_last_photo_element()
                self.momentsPage.click_album()
                
            with allure.step(f"4. 再次从相册勾选 {add_photo_count} 张新图片并点击发送/完成"):
                self._select_photos_and_confirm(count=add_photo_count, start_index=init_photo_count)
                
            with allure.step(f"5. 校验编辑页总图片数量更新为 {init_photo_count + add_photo_count} 张"):
                total_count = self.momentsPage.get_selected_photo_count()
                check.equal(total_count, init_photo_count + add_photo_count, f"❌ 追加图片后编辑页总图片数量不匹配")

        with allure.step("6. 发表多图动态：点击发布并校验"):
            self._publish_media_moment(actual_content)
            check.is_true(self.momentsPage.is_moment_contains_media(motype=1), f"❌ {case_id} 发布后首条朋友圈中未检测到图片媒体资源")
            check.is_false(self.momentsPage.is_moment_contains_media(motype=2), f"❌ {case_id} 图片发布后首条不应包含视频媒体资源")

        with allure.step("7. 后置清理：防御性删除发布的多图动态"):
            self._delete_test_moment(actual_content)


    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("发布朋友圈")
    @allure.title("朋友圈视频发布-状态：已完成")
    @pytest.mark.parametrize(
        "expect_overlimit_dialog",
        [
            pytest.param(False, id="正常发布"),
            pytest.param(True, id="超限弹窗处理后发布"),
        ],
    )
    def test_post_video_moment(self, expect_overlimit_dialog):
        """测试发布视频朋友圈 (精准选择视频多媒体，支持超限弹窗处理)"""
        title = "朋友圈视频发布-超限弹窗处理后发布" if expect_overlimit_dialog else "朋友圈视频发布-正常发布"
        test_content = f"视频测试_{title}_{int(time.time())}"
        
        with allure.step("1. 点击右上角相机按钮并选择从相册选择"):
            self.momentsPage.click_post_moments()
            self.momentsPage.click_album()
            
        with allure.step("2. 从相册勾选首个视频"):
            self.albumPage.click_only_video_checkbox_by_index(0)
            
        if expect_overlimit_dialog:
            with allure.step("2b. 触发并处理选择两个视频时的弹窗校验"):
                self.albumPage.click_album_image_by_index(1)
                has_dialog, msg = self.albumPage.handle_overlimit_dialog()
                check.is_true(has_dialog, "❌ 期望出现超限弹窗提示，但未检测到弹窗并处理")
                check.is_in("你最多只能选择1个视频", msg, f"❌ 超限警告提示不符合预期: {msg}")
                
        with allure.step("2c. 点击发送/完成"):
            self.albumPage.click_send_or_complete()
            
        with allure.step("3. 发表并校验视频动态"):
            self._publish_media_moment(test_content)
            check.is_true(self.momentsPage.is_moment_contains_media(motype=2), "❌ 发布后首条朋友圈中未检测到视频媒体资源")
            check.is_false(self.momentsPage.is_moment_contains_media(motype=1), "❌ 视频发布后首条不应包含图片媒体资源")
            
        with allure.step("4. 校验限制：朋友圈发布视频后，编辑页不可存在追加的加号按钮"):
            is_exist = self.momentsPage.is_last_photo_element()
            check.is_false(is_exist, f"❌ 发布视频后，最后一项不应该是加号")
            
        with allure.step("5. 后置清理：防御性删除发布的视频动态"):
            self._delete_test_moment(test_content)


    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story("发布朋友圈")
    @allure.title("朋友圈图片+视频发布限制-不支持图视频混选-状态：已完成")
    def test_post_video_moment_mixed_block(self):
        """测试朋友圈相册不支持图视频混选 (双向拦截校验)"""
        with allure.step("1. 点击右上角相机按钮并选择从相册选择"):
            self.momentsPage.click_post_moments()
            self.momentsPage.click_album()
            
        with allure.step("2. 【方向一】先勾选首张图片，再尝试勾选首个视频"):
            self.albumPage.click_only_photo_checkbox_by_index(0)
            self.albumPage.click_only_video_checkbox_by_index(0)
            
        with allure.step("3. 校验方向一：拦截提示及已选数量依然为 1"):
            has_dialog, msg = self.albumPage.handle_overlimit_dialog()
            check.is_true(has_dialog, "❌ 期望出现超限弹窗提示，但未检测到弹窗并处理")
            check.is_in("不能同时选择图片或视频", msg, f"❌ 超限警告提示不符合预期: {msg}")

        with allure.step("4. 重置状态：取消勾选首张图片，已选数量归零"):
            self.albumPage.click_only_photo_checkbox_by_index(0)
            selected_count = self.albumPage.get_selected_count()
            check.equal(selected_count, 0, "❌ 取消勾选失败，已选数量未归零")
            
        with allure.step("5. 【方向二】先勾选首个视频，再尝试勾选首张图片"):
            self.albumPage.click_only_video_checkbox_by_index(0)
            self.albumPage.click_only_photo_checkbox_by_index(0)

        with allure.step("6. 校验方向二：拦截提示及已选数量依然为 1"):
            has_dialog, msg = self.albumPage.handle_overlimit_dialog()
            check.is_true(has_dialog, "❌ 期望出现超限弹窗提示，但未检测到弹窗并处理")
            check.is_in("不能同时选择图片或视频", msg, f"❌ 超限警告提示不符合预期: {msg}")

        with allure.step("7. 后置清理：取消相册并返回朋友圈页面"):
            self.albumPage.click_album_cancel()
            self.momentsPage.wait_for_moments_page_load()


    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("删除朋友圈")
    @allure.title("删除朋友圈-状态：已完成")
    def test_delete_moment(self):
        """测试删除朋友圈"""
        test_content = f"删除测试临时动态"

        with allure.step("1. 前置造数据：发布一条文字朋友圈"):
            self._publish_test_moment(test_content)

        with allure.step("2. 删除朋友圈"):
            self._delete_test_moment(test_content)




