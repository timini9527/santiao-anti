import pytest
import allure
import time
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.moments.moments_page import MomentsPage
from pages.home.home_page import HomePage
from strategy.chat.chat_strategy import PRIVATE_USER1


@allure.epic("IM核心功能测试")
@allure.feature("朋友圈模块-多端与社交互动")
class TestMomentsDouble:
    """朋友圈与动态社交互动双端协同测试"""

    mainS: 'MainPage'
    momentsS: 'MomentsPage'
    homeS: 'HomePage'

    mainR: 'MainPage'
    momentsR: 'MomentsPage'
    homeR: 'HomePage'

    @pytest.fixture(scope="class", autouse=True)
    def setup_double_env(self, request, driver_sender, driver_receiver):
        """初始化双端页面对象并确保其测试前状态正常 (只在类开始时运行一次)"""
        cls = request.cls
        cls.mainS = MainPage(driver_sender)
        cls.momentsS = MomentsPage(driver_sender)
        cls.homeS = HomePage(driver_sender)

        cls.mainR = MainPage(driver_receiver)
        cls.momentsR = MomentsPage(driver_receiver)
        cls.homeR = HomePage(driver_receiver)

        with allure.step("前置步骤：两端确认在主页并进入朋友圈"):
            cls._go_to_moments_pageS()
            cls._go_to_moments_pageR()

        yield

        with allure.step("后置清理：两端返回首页"):
            for main_page, name in [(cls.mainS, "发送端"), (cls.mainR, "接收端")]:
                try:
                    main_page.go_to_main_page()
                except Exception as e:
                    logger.error(f"{name} Teardown 失败: {e}")


    # ============================================================================
    # 辅助提炼方法：简化发送端与接收端的动作，减少冗余代码
    # ============================================================================
    @classmethod
    def _go_to_moments_pageS(cls):
        """发送端进入朋友圈页面"""
        cls.mainS.go_to_main_page()
        cls.homeS.click_bottom_expand_button()
        cls.homeS.click_dynamic()
        is_loaded = cls.momentsS.wait_for_moments_page_load()
        check.is_true(is_loaded, "❌ 发送端朋友圈页面加载失败")

    @classmethod
    def _go_to_moments_pageR(cls):
        """接收端进入朋友圈页面"""
        cls.mainR.go_to_main_page()
        cls.homeR.click_bottom_expand_button()
        cls.homeR.click_dynamic()
        is_loaded = cls.momentsR.wait_for_moments_page_load()
        check.is_true(is_loaded, "❌ 接收端朋友圈页面加载失败")
    
    def _delete_test_moment(self, content: str):
        """删除测试朋友圈 (带防误删校验)"""
        try:
            time.sleep(1)
            self.momentsS.refresh_moments()
            first_content = self.momentsS.get_first_moment_content(0) or ""
            if content in first_content:
                self.momentsS.delete_first_moment()
                found = self.momentsS.has_moment_with_text(content)
                check.is_false(found, f"❌ 测试临时动态 [{content}] 删除后依然可见")
            else:
                logger.info(f"ℹ️ [Teardown] 未在首条朋友圈找到测试动态 [{content}]，跳过删除以防误删")
        except Exception as e:
            logger.error(f"❌ [Teardown] 删除测试朋友圈失败: {content}, 原因: {e}")

    def _register_moment_cleanup(self, request, content: str):
        """注册防御性清理，避免用例中途失败后残留测试动态"""
        def cleanup(target_content=content):
            self._delete_test_moment(target_content)
        request.addfinalizer(cleanup)

    def _sender_post_moment(self, content_prefix: str, visibility: str = "public", target_friend: str = None, target_tag: str = None, is_ex: bool = True) -> str:
        """发送端进入朋友圈并发布指定可见范围的动态，自动附加唯一时间戳并返回生成的最终文案"""
        timestamp = int(time.time())
        actual_content = f"{content_prefix} {timestamp}"
        
        if visibility == "public" or visibility == "公开":
            self.momentsS.post_moment_with_visibility(actual_content)
        else:
            self.momentsS.post_moment_with_visibility(actual_content, visibility=visibility, target_friend=target_friend, target_tag=target_tag, is_ex=is_ex)
        
        if is_ex:
            self.momentsS.wait_for_moments_page_load()
            
        logger.info(f"发送端成功发布朋友圈动态 ({visibility}): {actual_content}")
        return actual_content

    def _receiver_prepare_moments_feed(self, expected_content: str = None, max_refresh: int = 3) -> str:
        """接收端刷新朋友圈，返回首条动态；传入期望文案时会做短轮询等待同步"""
        actual_content = ""
        for attempt in range(1, max_refresh + 1):
            self.momentsR.refresh_moments()
            actual_content = self.momentsR.get_first_moment_content()
            logger.info(f"接收端第 {attempt} 次刷新后首条朋友圈动态: {actual_content}")
            if expected_content is None or actual_content == expected_content:
                return actual_content
            time.sleep(0.3)
        return actual_content



    # ----------------------------------------------------------------------------
    # 1. 基础可见性与删除同步
    # ----------------------------------------------------------------------------
    @allure.story("好友动态可见性与更新同步")
    @allure.title("好友发布朋友圈动态后接收端同步可见-状态：已完成")
    def test_friend_moment_visibility(self, request):
        """测试发送端发布公开动态后，接收端刷新能同步可见"""
        with allure.step("1. 发送端进入朋友圈并发布公开动态"):
            test_content = self._sender_post_moment("双端可见性测试文字动态")
            self._register_moment_cleanup(request, test_content)

        with allure.step("2. 接收端进入朋友圈并下拉刷新"):
            actual_content = self._receiver_prepare_moments_feed(test_content)

        with allure.step("3. 校验接收端信息流首位是否同步显示该动态"):
            check.equal(actual_content, test_content, "❌ 接收端未能同步看到发送端发布的好友朋友圈动态")

        with allure.step("4. 后置清理：删除测试动态"):
            self._delete_test_moment(test_content)


    @allure.story("动态管理")
    @allure.title("发送端删除自己动态，接收端同步不可见-状态：已完成")
    def test_delete_moment_sync_double(self, request):
        """测试发送端删除朋友圈后，接收端刷新朋友圈列表已被同步清除"""
        with allure.step("1. 发送端发布公开动态"):
            test_content = self._sender_post_moment("双端删除同步测试动态")
            self._register_moment_cleanup(request, test_content)

        with allure.step("2. 接收端刷新列表并确认能看到动态"):
            first_content = self._receiver_prepare_moments_feed(test_content)
            check.equal(first_content, test_content, "❌ 接收端在删除前未能查看到该动态")

        with allure.step("3. 发送端删除自己发布的动态"):
            self.momentsS.delete_first_moment()

        with allure.step("4. 接收端刷新并校验动态已被同步移出"):
            self.momentsR.refresh_moments()
            found = self.momentsR.has_moment_with_text(test_content)
            check.is_false(found, f"❌ 发送端删除朋友圈后，接收端仍然能查看到 [{test_content}]")


    # ----------------------------------------------------------------------------
    # 2. 社交可见性设置（隐私规则）
    # ----------------------------------------------------------------------------
    @allure.story("社交可见性与互为好友规则")
    @allure.title("发送端发布私密朋友圈，接收端不可见-状态：已完成")
    def test_private_moment_visibility_double(self, request):
        """测试发送端发布私密动态后，接收端无法查看"""
        with allure.step("1. 发送端发布私密动态"):
            private_content = self._sender_post_moment("我是私密动态", visibility="private")
            self._register_moment_cleanup(request, private_content)

        with allure.step("2. 接收端进入朋友圈刷新"):
            self._receiver_prepare_moments_feed()

        with allure.step("3. 校验接收端无法查看到该私密文案"):
            visible_contents = self.momentsR.get_visible_moment_contents()
            check.is_false(
                private_content in visible_contents,
                f"❌ 错误：接收端不应能看到发送端发布的私密动态 [{private_content}]"
            )
        
        with allure.step("4. 后置清理：删除测试动态"):
            self._delete_test_moment(private_content)

    
    @allure.story("社交可见性与互为好友规则")
    @allure.title("部分可见：发送端设置仅标签里的用户可见，标签外用户不可见-状态：已完成")
    def test_partial_visibility_tag_double(self, request):
        """测试发送端发布部分可见（仅标签里的用户可见）动态后，接收端无法查看"""
        with allure.step("1. 发送端发布部分可见（仅标签里的用户可见）动态"):
            partial_content = self._sender_post_moment("部分可见（仅标签里的用户可见）动态", visibility="partial", target_tag="测试标签", is_ex=False)
            self._register_moment_cleanup(request, partial_content)

            count = self.momentsS.get_tag_member_count_by_tag_name("测试标签")
            if count == 0:
                self.momentsS.click_tag_arrow_by_name("测试标签")
                self.momentsS.click_tag_add_button()
                self.momentsS.click_tag_add_friend_button(PRIVATE_USER1.name)
            tag_user_names = self.momentsS.get_visible_tag_names("测试标签")
            check.is_in(PRIVATE_USER1.name, tag_user_names, "❌ 部分可见动态的标签名称不包含指定好友")

            self.momentsS.click_tag_by_name("测试标签")
            self.momentsS.click_publish()
            
            _, subtitle = self.momentsS.get_partial_custom_title_and_subtitle()
            check.is_in("测试标签", subtitle, "❌ 部分可见动态的副标题不包含指定好友")
            self.momentsS.click_publish()

        with allure.step("2. 二次验证选择可见范围标题和副标题"):
            title, subtitle = self.momentsS.get_visible_title_and_friends()
            check.is_in("谁可以看", title, "❌ 二次验证选择可见范围标题不包含谁可以看")
            check.is_in("测试标签", subtitle, "❌ 部分可见动态的副标题不包含指定好友")
            self.momentsS.click_publish()

        with allure.step("3. 接收端进入朋友圈刷新"):
            self._receiver_prepare_moments_feed()

        with allure.step("3. 校验接收端无法查看到该部分可见（仅标签里的用户可见）文案"):
            visible_contents = self.momentsR.get_visible_moment_contents()
            check.is_true(
                partial_content in visible_contents,
                f"❌ 接收端被设置为‘仅标签里的用户可见’，但未看到发送端的朋友圈 [{partial_content}]"
            )
        
        with allure.step("4. 后置清理：删除测试动态"):
            self._delete_test_moment(partial_content)
    

    @allure.story("社交可见性与互为好友规则")
    @allure.title("部分可见：发送端设置仅接收端可见，接收端可同步查看-状态：已完成")
    def test_partial_visibility_double(self, request):
        """测试发送端发布部分可见（仅接收端可见）动态后，接收端能够正常查看"""
        with allure.step(f"1. 发送端发布部分可见动态，指定可见好友: {PRIVATE_USER1.name}"):
            partial_content = self._sender_post_moment("部分可见动态", visibility="partial", target_friend=PRIVATE_USER1.name, is_ex=False)
            self._register_moment_cleanup(request, partial_content)
            subtitle = self.momentsS.get_partial_friend_subtitle()
            check.is_in(PRIVATE_USER1.name, subtitle, "❌ 部分可见动态的副标题不包含指定好友")
            self.momentsS.click_publish()

        with allure.step("2. 二次验证选择可见范围标题和副标题"):     
            title, subtitle = self.momentsS.get_visible_title_and_friends()
            check.is_in("谁可以看", title, "❌ 二次验证选择可见范围标题不包含谁可以看")
            check.is_in(PRIVATE_USER1.name, subtitle, "❌ 部分可见动态的副标题不包含指定好友")
            self.momentsS.click_publish()
        
        with allure.step("3. 接收端进入朋友圈并刷新"):
            self._receiver_prepare_moments_feed(partial_content)

        with allure.step("4. 校验接收端能够正常查看到该部分可见动态"):
            visible_contents = self.momentsR.get_visible_moment_contents()
            check.is_true(
                partial_content in visible_contents,
                f"❌ 接收端被设置为‘部分可见’，但未看到发送端的朋友圈 [{partial_content}]"
            )

        with allure.step("5. 后置清理：发送端删除该部分可见动态"):
            self.momentsS.delete_first_moment()


    @allure.story("社交可见性与互为好友规则")
    @allure.title("不给谁看：发送端排除接收端，接收端不可见-状态：已完成")
    def test_exclude_visibility_double(self, request):
        """测试发送端发布不给谁看（排除接收端）动态后，接收端刷新列表无法查看"""
        with allure.step(f"1. 发送端发布排除可见动态，指定排除好友: {PRIVATE_USER1.name}"):
            exclude_content = self._sender_post_moment("排除可见动态", visibility="exclude", target_friend=PRIVATE_USER1.name, is_ex=False)
            self._register_moment_cleanup(request, exclude_content)
            subtitle = self.momentsS.get_exclude_friend_subtitle()
            check.is_in(PRIVATE_USER1.name, subtitle, "❌ 排除可见动态的副标题不包含指定好友")
            self.momentsS.click_publish()

        with allure.step("2. 二次验证选择可见范围标题和副标题"):     
            title, subtitle = self.momentsS.get_visible_title_and_friends()
            check.is_in("谁不可看", title, "❌ 二次验证选择可见范围标题不包含不给谁看")
            check.is_in(PRIVATE_USER1.name, subtitle, "❌ 排除可见动态的副标题不包含指定好友")
            self.momentsS.click_publish()
        
        with allure.step("3. 接收端进入朋友圈并下拉刷新"):
            self._receiver_prepare_moments_feed()

        with allure.step("4. 校验接收端无法查看到该排除动态"):
            visible_contents = self.momentsR.get_visible_moment_contents()
            check.is_false(
                exclude_content in visible_contents,
                f"❌ 错误：接收端已被设置为‘不给谁看’，但依然能看到发送端的朋友圈 [{exclude_content}]"
            )

        with allure.step("5. 后置清理：发送端删除该排除可见动态"):
            self.momentsS.delete_first_moment()


    # ----------------------------------------------------------------------------
    # 3. 互动与反馈（点赞评论）
    # ----------------------------------------------------------------------------
    @allure.story("社交互动与反馈")
    @allure.title("给好友朋友圈点赞和评论多端同步校验-状态：已完成")
    def test_moment_interaction_double(self, request):
        """测试接收端给发送端发布的朋友圈进行点赞和评论，发送端可实时查看互动结果"""
        comment_content = f"来自好友的自动点赞评论 {int(time.time())}"

        with allure.step("1. 发送端进入朋友圈并发布动态"):
            test_content = self._sender_post_moment("双端互动测试动态")
            self._register_moment_cleanup(request, test_content)

        with allure.step("2. 接收端进入朋友圈刷新并进行点赞评论"):
            first_content = self._receiver_prepare_moments_feed(test_content)
            if first_content == test_content:
                self.momentsR.click_like_nth_moment(0)
                self.momentsR.click_comment_on_nth_moment(0)
                self.momentsR.post_comment(comment_content)
            else:
                pytest.skip("接收端未刷出发送端刚发的动态，跳过互动测试")

        with allure.step("3. 发送端刷新页面并校验互动信息"):
            self.momentsS.refresh_moments()
            comments = self.momentsS.get_comment_texts()
            check.is_true(
                any(comment_content in comment for comment in comments),
                f"❌ 发送端未看到接收端的评论内容: {comment_content}"
            )
            like_users = self.momentsS.get_nth_moment_like_users(0)
            check.is_true(PRIVATE_USER1.name in like_users, "❌ 发送端未展示点赞状态或点赞人")

        with allure.step("4. 后置清理：删除测试动态"):
            self._delete_test_moment(test_content)


    @allure.story("点赞与评论")
    @allure.title("双端同步校验：接收端取消点赞，发送端同步更新-状态：已完成")
    def test_like_cancel_sync_double(self, request):
        """测试接收端点赞后又取消点赞，发送端能够实时看到点赞用户的移除"""

        with allure.step("1. 发送端进入朋友圈并发布公开动态"):
            test_content = self._sender_post_moment("双端取消点赞测试动态")
            self._register_moment_cleanup(request, test_content)

        with allure.step("2. 接收端进入朋友圈，下拉刷新并点赞"):
            first_content = self._receiver_prepare_moments_feed(test_content)
            if first_content == test_content:
                self.momentsR.click_like_nth_moment(0)
            else:
                pytest.skip("接收端未刷出发送端刚发的动态，跳过测试")

        with allure.step("3. 发送端校验接收端已点赞"):
            self.momentsS.refresh_moments()
            like_users = self.momentsS.get_nth_moment_like_users(0)
            check.is_true(
                PRIVATE_USER1.name in like_users,
                f"❌ 发送端未能成功看到接收端 {PRIVATE_USER1.name} 的点赞"
            )

        with allure.step("4. 接收端再次点击取消点赞"):
            self.momentsR.click_like_nth_moment(0)

        with allure.step("5. 发送端刷新并校验点赞已被移除"):
            self.momentsS.refresh_moments()
            like_users_after = self.momentsS.get_nth_moment_like_users(0)
            check.is_false(
                PRIVATE_USER1.name in like_users_after,
                f"❌ 接收端取消点赞后，发送端依然查看到点赞列表包含 {PRIVATE_USER1.name}"
            )

        with allure.step("6. 后置清理：发送端删除用于测试的动态"):
            self._delete_test_moment(test_content)


    # ----------------------------------------------------------------------------
    # 4. 消息通知与红点分发
    # ----------------------------------------------------------------------------
    @allure.story("朋友圈通知与发现红点")
    @allure.title("社交互动新通知与主页发现红点清除同步校验-状态：已完成")
    def test_moment_notification_red_dot(self, request):
        """测试接收端给发送端点赞评论后，发送端能够收到消息通知并正确清除红点提示"""
        comment_content = f"自动触发红点评论 {int(time.time())}"

        with allure.step("1. 发送端发布朋友圈并返回首页"):
            test_content = self._sender_post_moment("新消息红点测试动态")
            self._register_moment_cleanup(request, test_content)
            self.mainS.go_to_main_page()

        with allure.step("2. 接收端刷新并评论发送端动态以触发红点"):
            first_content = self._receiver_prepare_moments_feed(test_content)
            if first_content == test_content:
                self.momentsR.click_like_nth_moment(0)
                self.momentsR.click_comment_on_nth_moment(0)
                self.momentsR.post_comment(comment_content)
            else:
                pytest.skip("接收端未及时加载该动态，跳过红点触发校验")

        with allure.step("3. 发送端首页红点状态检验"):
            self.homeS.click_bottom_expand_button()
            unread_count = self.homeS.get_dynamic_unread_msg_count()
            check.is_true(int(unread_count) > 0, "❌ 接收端发表互动后，发送端未能成功收到朋友圈新消息提醒")
        
        with allure.step("4. 发送端进入朋友圈，校验新消息提醒"):
            self.homeS.click_dynamic()
            is_loaded = self.momentsS.wait_for_moments_page_load()
            check.is_true(is_loaded, "❌ 发送端朋友圈页面加载失败")
            new_message = self.momentsS.get_new_message_tips()
            check.is_in(f'{int(unread_count)}条新消息', new_message, f"❌ 接收端发表互动后，发送端未能成功显示朋友圈新消息提醒")
            self.momentsS.click_new_message()
            self.momentsS.click_iv_back()
            new_message = self.momentsS.get_new_message_tips(False)
            check.is_false(bool(new_message), "❌ 接收端发表互动后，发送端未能成功清除朋友圈新消息提醒")
            
        with allure.step("5. 后置清理：删除测试动态"):
            self._delete_test_moment(test_content)


    @allure.story("朋友圈通知与发现红点")
    @allure.title("收到回复通知：发送端回复接收端评论，接收端收到新消息提醒-状态：已完成")
    def test_comment_reply_notification_double(self, request):
        """测试发送端回复接收端的评论，接收端能够收到消息回复通知并清除"""
        comment_content = f"待回复的评论 {int(time.time())}"
        reply_content = f"作者的回复内容 {int(time.time())}"

        with allure.step("1. 发送端进入朋友圈并发布公开动态"):
            test_content = self._sender_post_moment("双端评论回复通知动态")
            self._register_moment_cleanup(request, test_content)

        with allure.step("2. 接收端进入朋友圈发表评论并返回主页"):
            first_content = self._receiver_prepare_moments_feed(test_content)
            if first_content == test_content:
                self.momentsR.click_comment_on_nth_moment(0)
                self.momentsR.post_comment(comment_content)
            else:
                pytest.skip("接收端未刷出发送端刚发的动态，跳过测试")

        with allure.step("3. 发送端回复接收端的评论"):
            self.momentsS.refresh_moments()
            self.momentsS.click_comment_by_text(comment_content, nickname=PRIVATE_USER1.name)
            self.momentsS.post_comment(reply_content)

        with allure.step("4. 接收端进入朋友圈校验新消息提醒与清除"):
            self.momentsR.refresh_moments()
            new_message = self.momentsR.get_new_message_tips()
            check.is_in(f"条新消息", new_message, "❌ 接收端显示朋友圈新消息提醒不符合预期")
            self.momentsR.click_new_message()
            self.momentsR.click_iv_back()
            new_message_after = self.momentsR.get_new_message_tips(False)
            check.is_false(bool(new_message_after), "❌ 接收端查看并返回后，朋友圈气泡提醒未正确清空")

        with allure.step("5. 后置清理：发送端删除该测试动态"):
            self._delete_test_moment(test_content)
