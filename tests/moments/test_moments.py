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
@allure.feature("朋友圈模块-发布与互动")
class TestMoments:
    _publish_cases_data = load_yaml_data("moments/moments_data.yaml")["test_cases"]
    _comment_cases_data = load_yaml_data("moments/moments_data.yaml")["comment_cases"]
    _shared_comment_moment_content = None
    _comment_test_counter = 0

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

        try:
            if self.momentsPage.is_publish_editor_displayed():
                logger.warning("⚠️ 用例执行结束，但仍留在发布编辑页，强行执行返回及清理...")
                self.momentsPage.click_iv_back()
                try:
                    self.momentsPage.confirm_delete_moment()
                except Exception:
                    pass
                self.momentsPage.wait_for_moments_page_load(raise_exception=False)
        except Exception as e:
            logger.error(f"方法级 Teardown 恢复朋友圈状态失败: {e}")
    

    def _publish_test_moment(self, content: str) -> str:
        """发布文本测试朋友圈，返回包含时间戳的实际正文"""
        timestamp = int(time.time())
        actual_content = content + str(timestamp)
        self.momentsPage.post_text_moment(actual_content)
        toast = self.momentsPage.get_toast("发布成功")
        check.equal(toast, "发布成功", f"❌ 朋友圈发布失败")

        # TODO: Android端有BUG，每次点击发布后必须下拉刷新才能看到最新发布
        self.momentsPage.refresh_moments()
        check.equal(actual_content, self.momentsPage.get_first_moment_content(), f"❌ 朋友圈未能正常发布测试动态{actual_content}")
        return actual_content
        

    def _delete_test_moment(self, content: str):
        """删除测试朋友圈 (带防误删校验)"""
        first_content = self.momentsPage.get_first_moment_content()
        if content in first_content:
            self.momentsPage.delete_first_moment()
            found = self.momentsPage.has_moment_with_text(content)
            check.is_false(found, f"❌ 测试临时动态 [{content}] 删除后依然可见")
        else:
            logger.warning(f"⚠️ [Teardown] 首条朋友圈内容 [{first_content}] 与要删内容 [{content}] 不匹配，跳过删除以防误删他人数据")
    
        
    @pytest.fixture
    def temp_like_moment(self):
        """点赞与取消点赞用例专用的临时朋友圈"""
        actual_content = self._publish_test_moment("点赞测试动态_")
        yield actual_content
        with allure.step("后置清理：删除点赞测试临时动态"):
            self._delete_test_moment(actual_content)

    @pytest.fixture
    def comment_shared_moment(self):
        """参数化评论用例共享的临时朋友圈动态"""
        self.__class__._comment_test_counter += 1
        total_cases = len(self.__class__._comment_cases_data)
        
        if self.__class__._shared_comment_moment_content is None:
            actual_published = self._publish_test_moment("评论测试专用动态_")
            self.__class__._shared_comment_moment_content = actual_published
            
        yield self.__class__._shared_comment_moment_content
        
        if self.__class__._comment_test_counter >= total_cases:
            with allure.step("终期清理：所有评论参数化用例运行完毕，删除共享朋友圈"):
                if self.__class__._shared_comment_moment_content:
                    try:
                        self._delete_test_moment(self.__class__._shared_comment_moment_content)
                    except Exception as e:
                        logger.error(f"⚠️ 清理评论专用朋友圈失败: {e}")
                    finally:
                        self.__class__._shared_comment_moment_content = None
                        self.__class__._comment_test_counter = 0

    @pytest.fixture
    def temp_empty_comment_moment(self):
        """空评论测试专用的临时朋友圈"""
        actual_content = self._publish_test_moment("空评论测试临时动态_")
        yield actual_content
        with allure.step("后置清理：删除空评论测试临时动态"):
            self._delete_test_moment(actual_content)


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
                check.equal(expected_toast, empty_toast, f"❌ {case_id} 空内容，朋友圈发布失败")
            elif expected_behavior == "blocked":
                blocked_toast = self.momentsPage.get_toast(expected_toast)
                check.equal(expected_toast, blocked_toast, f"❌ {case_id} 敏感词，朋友圈发布失败")
            else:
                toast = self.momentsPage.get_toast("发布成功")
                check.equal(toast, "发布成功", f"❌ {case_id} 正常发布朋友圈失败")
                self.momentsPage.wait_for_moments_page_load()
                # TODO: Android端有BUG，每次点击发布后必须下拉刷新才能看到最新发布
                self.momentsPage.refresh_moments()
            
        if expected_behavior in ["success", "truncated"]:
            with allure.step("3. 校验发布成功后是否停留在朋友圈页面"):
                self.momentsPage.click_expand_or_shrink_moment(is_expand=is_expand)

        if expected_behavior == "success":
            with allure.step("4. 校验动态是否完整显示在列表首位"):
                actual_content = self.momentsPage.get_first_moment_content()
                check.equal(actual_content, content, f"❌ {case_id} 正常发布朋友圈内容不匹配")

        elif expected_behavior == "empty":
            with allure.step("4. 校验仍停留在发布编辑页"):
                is_still_editing = self.momentsPage.is_publish_editor_displayed()
                check.is_true(is_still_editing, "❌ 空内容朋友圈不应被成功发布")
                if is_still_editing:
                    self.momentsPage.click_iv_back()
                    self.momentsPage.wait_for_moments_page_load()

        elif expected_behavior == "truncated":
            with allure.step("4. 校验发布成功后列表首条动态被自动截断限制为 999 字符"):
                actual_content = self.momentsPage.get_first_moment_content()
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


    @allure.story("发布朋友圈")
    @pytest.mark.parametrize(
        "case_id, title, init_photo_count, add_photo_count, expected_behavior",
        [
            ("MOMENT_PUB_002", "发布单张图片朋友圈", 1, 0, "success"),
            ("MOMENT_PUB_003", "选择图片超过上限9张拦截提示", 10, 0, "overlimit_toast"),
            ("MOMENT_PUB_004", "已选择图片少于9张时继续添加", 3, 2, "add_more_and_publish")
        ]
    )
    def test_post_image_moment_scenarios(self, request, case_id, title, init_photo_count, add_photo_count, expected_behavior):
        """测试多图发布朋友圈的各种场景 (包含单图发布、超限拦截和追加图片)"""
        allure.dynamic.title(f"{case_id} - {title}")
        
        from pages.common.album_page import CommonAlbumPage
        album_page = CommonAlbumPage(self.momentsPage.driver)
        
        test_text = f"图片测试_{case_id}_"
        actual_content = f"{test_text}{int(time.time())}"
        
        try:
            with allure.step("1. 点击右上角相机按钮并选择从相册选择"):
                self.momentsPage.click_post_moments()
                self.momentsPage.click_album()
                
            if expected_behavior == "success":
                with allure.step("2. 勾选第一张图片并点击发送/完成"):
                    album_page.click_photo_checkbox_by_index(0)
                    album_page.click_send_or_complete()
                    
                with allure.step("3. 在朋友圈编辑页输入文字描述并点击发表"):
                    self.momentsPage.input_moments_content(actual_content)
                    self.momentsPage.click_publish()
                    
                with allure.step("4. 校验朋友圈提示发布成功，且列表中首条内容匹配"):
                    toast = self.momentsPage.get_toast("发布成功")
                    check.equal(toast, "发布成功", "❌ 朋友圈发布图片动态未能弹出‘发布成功’提示")
                    self.momentsPage.wait_for_moments_page_load()
                    self.momentsPage.refresh_moments()
                    first_content = self.momentsPage.get_first_moment_content()
                    check.equal(first_content, actual_content, "❌ 朋友圈列表中最新发布的图片动态文字不匹配")
                    
            elif expected_behavior == "overlimit_toast":
                with allure.step("2. 依次勾选 9 张图片，并尝试勾选第 10 张图片"):
                    # 循环勾选前 9 张图片
                    for i in range(9):
                        album_page.click_photo_checkbox_by_index(i)
                    # 尝试点击第 10 张
                    album_page.click_photo_checkbox_by_index(9)
                    
                with allure.step("3. 验证选择超过 9 张的限制提示"):
                    toast = self.momentsPage.get_toast("最多只能选择9张", timeout=2)
                    if not toast:
                        has_dialog = album_page.handle_overlimit_dialog()
                        check.is_true(has_dialog, "❌ 勾选第10张图片时，未检测到超限 Toast 提示或弹窗警告")
                    else:
                        check.is_true("9" in toast or "最多" in toast, f"❌ 超限 Toast 提示不符合预期: {toast}")
                        
                with allure.step("4. 点击发送/完成并输入文字发表"):
                    album_page.click_send_or_complete()
                    self.momentsPage.input_moments_content(actual_content)
                    self.momentsPage.click_publish()
                    
                with allure.step("5. 校验朋友圈提示发布成功，且列表中首条内容匹配"):
                    toast = self.momentsPage.get_toast("发布成功")
                    check.equal(toast, "发布成功", "❌ 朋友圈发布图片动态未能弹出‘发布成功’提示")
                    self.momentsPage.wait_for_moments_page_load()
                    self.momentsPage.refresh_moments()
                    first_content = self.momentsPage.get_first_moment_content()
                    check.equal(first_content, actual_content, "❌ 朋友圈列表中最新发布的图片动态文字不匹配")
                    
            elif expected_behavior == "add_more_and_publish":
                with allure.step(f"2. 首次勾选 {init_photo_count} 张图片并返回编辑页"):
                    for i in range(init_photo_count):
                        album_page.click_photo_checkbox_by_index(i)
                    album_page.click_send_or_complete()
                    
                with allure.step(f"3. 校验当前编辑页已选图片为 {init_photo_count} 张，并点击加号继续添加"):
                    current_count = self.momentsPage.get_published_photo_count()
                    check.equal(current_count, init_photo_count, f"❌ 编辑页初始展示图片数量与预期不符")
                    self.momentsPage.click_add_more_photos()
                    
                with allure.step(f"4. 再次从相册勾选 {add_photo_count} 张新图片并点击发送/完成"):
                    # 避免勾选已经选过的图片，我们从已选数量开始往后勾选
                    for i in range(init_photo_count, init_photo_count + add_photo_count):
                        album_page.click_photo_checkbox_by_index(i)
                    album_page.click_send_or_complete()
                    
                with allure.step(f"5. 校验编辑页总图片数量更新为 {init_photo_count + add_photo_count} 张"):
                    total_count = self.momentsPage.get_published_photo_count()
                    check.equal(total_count, init_photo_count + add_photo_count, f"❌ 追加图片后编辑页总图片数量不匹配")
                    
                with allure.step("6. 输入描述文本并点击发表"):
                    self.momentsPage.input_moments_content(actual_content)
                    self.momentsPage.click_publish()
                    
                with allure.step("7. 校验朋友圈列表中首条内容匹配"):
                    toast = self.momentsPage.get_toast("发布成功")
                    check.equal(toast, "发布成功", "❌ 朋友圈发布多图动态未能弹出‘发布成功’提示")
                    self.momentsPage.wait_for_moments_page_load()
                    self.momentsPage.refresh_moments()
                    first_content = self.momentsPage.get_first_moment_content()
                    check.equal(first_content, actual_content, "❌ 朋友圈列表中最新发布的图片动态文字不匹配")
                    
        finally:
            with allure.step("后置清理：防御性删除发布的多图动态"):
                try:
                    self._delete_test_moment(actual_content)
                except Exception as e:
                    logger.warning(f"⚠️ 清理多图朋友圈失败: {e}")


    @allure.story("删除朋友圈")
    @allure.title("删除朋友圈-状态：已完成")
    def test_delete_moment(self):
        """测试删除朋友圈"""
        test_content = f"删除测试临时动态"

        with allure.step("1. 前置造数据：发布一条文字朋友圈"):
            self._publish_test_moment(test_content)

        with allure.step("2. 删除朋友圈"):
            self._delete_test_moment(test_content)


    @allure.story("点赞与评论")
    @allure.title("点赞并取消点赞-状态：已完成")
    def test_like_and_cancel_moment(self, temp_like_moment):
        """测试对朋友圈动态点赞后可再次取消点赞（自产自销，数据闭环）"""

        with allure.step("1. 获取该动态的初始点赞状态（预期为空）"):
            before_like = self.momentsPage.get_nth_moment_like_users(0)
            check.equal(before_like, [], "❌ 新发布的动态点赞状态应该为空")

        with allure.step("2. 正常执行点赞"):
            self.momentsPage.click_like_nth_moment(0)
            after_like = self.momentsPage.get_nth_moment_like_users(0)
            check.not_equal(after_like, before_like, "❌ 点赞后点赞状态未发生变化")

        with allure.step("3. 正常执行取消点赞"):
            self.momentsPage.click_like_nth_moment(0)
            after_cancel = self.momentsPage.get_nth_moment_like_users(0)
            check.equal(after_cancel, before_like, "❌ 取消点赞后状态未恢复到点赞前")


    @allure.story("点赞与评论")
    @allure.title("评论朋友圈-{case_id}-状态：已完成")
    @pytest.mark.parametrize(
        "case_data",
        _comment_cases_data,
        ids=lambda x: x["desc"]
    )
    def test_comment_moment(self, case_data, comment_shared_moment):
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
                    check.equal(expected_toast, limit_toast, f"❌ {case_id} 超长评论未弹出字数限制提示")

                self.momentsPage.send_comment()

                if expected_behavior == "blocked":
                    blocked_toast = self.momentsPage.get_toast(expected_toast)
                    check.equal(expected_toast, blocked_toast, f"❌ {case_id} 敏感词评论未被正确拦截")
                
                time.sleep(1)

            if expected_behavior == "success":
                with allure.step("4. 校验评论是否成功展示在列表中"):
                    comments = self.momentsPage.get_comment_texts()
                    check.is_true(
                        any(comment_text in comment for comment in comments),
                        f"❌ {case_id} 未在列表中找到已发表的评论: {comment_text}"
                    )
            elif expected_behavior == "truncated":
                with allure.step("4. 校验超长评论是否被自动截断为 999 字符"):
                    comments = self.momentsPage.get_comment_texts()
                    truncated_text = comment_text[:999]
                    
                    matched_comment = next((c for c in comments if truncated_text in c), "")
                    check.is_true(bool(matched_comment), f"❌ {case_id} 未在列表中找到截断后的 999 字符评论")
                    
                    if matched_comment:
                        content_part = matched_comment.split(":", 1)[-1].strip()
                        content_part = content_part.split("：", 1)[-1].strip()
                        check.equal(len(content_part), 999, f"❌ {case_id} 评论长度未被截断为 999 字符")

            elif expected_behavior == "blocked":
                with allure.step("4. 校验敏感词评论未展示在列表中"):
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


    @allure.story("点赞与评论")
    @allure.title("评论为空不可发送-状态：已完成")
    def test_empty_comment_cannot_send(self, temp_empty_comment_moment):
        """测试空评论不能成功发送"""

        with allure.step("1. 获取发送空评论前的评论列表"):
            before_comments = self.momentsPage.get_comment_texts(2, False)

        with allure.step("2. 点击评论按钮并不输入内容尝试点击发送"):
            self.momentsPage.click_comment_on_nth_moment(0)
            self.momentsPage.send_comment()

        with allure.step("3. 校验评论列表未新增空评论且未成功发送"):
            after_comments = self.momentsPage.get_comment_texts(2, False)
            check.equal(after_comments, before_comments, "❌ 空评论不应被成功发送，评论列表应当保持不变")




    @allure.story("点赞与评论")
    @allure.title("MOMENT_INTER_005 - 删除自己的评论")
    def test_delete_own_comment(self, request):
        """测试自己发表的评论可以被点击并成功删除 (数据闭环)"""
        # 前置条件：发布专属的临时朋友圈作为操作容器，防止对正常数据进行污染
        test_moment_content = self._publish_test_moment("删除评论测试动态_")
        
        # 注册 Teardown：保证测试动态最终一定会被清理 (带防御性匹配)
        request.addfinalizer(lambda: self._delete_test_moment(test_moment_content))
        
        timestamp = int(time.time())
        test_comment = f"待删除的自发评论 {timestamp}"

        # 注册 Teardown：兜底清理测试评论，避免测试在中途 crash 导致评论污染动态
        def cleanup_comment():
            try:
                self.momentsPage.delete_own_comment_with_confirm(test_comment)
            except Exception:
                pass
        request.addfinalizer(cleanup_comment)

        with allure.step("1. 发表一条新评论"):
            # 为首位动态点击评论并发表
            self.momentsPage.click_comment_on_nth_moment(0)
            self.momentsPage.post_comment(test_comment)
            time.sleep(1)

        with allure.step("2. 确认评论列表中出现了该条评论"):
            comments = self.momentsPage.get_comment_texts(raise_exception=False)
            check.is_true(
                any(test_comment in comment for comment in comments),
                f"❌ 未成功发表待删除评论: {test_comment}"
            )

        with allure.step("3. 点击该条评论，触发删除并二次确认"):
            self.momentsPage.delete_own_comment_with_confirm(test_comment)
            time.sleep(1)

        with allure.step("4. 校验该评论已从列表中消失"):
            comments_after = self.momentsPage.get_comment_texts(raise_exception=False)
            check.is_false(
                any(test_comment in comment for comment in comments_after),
                f"❌ 评论 [{test_comment}] 删除后依然可见"
            )



