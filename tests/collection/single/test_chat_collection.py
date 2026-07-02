import allure
import pytest
import pytest_check as check
from pages.main.main_page import MainPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.core.chat_long_press_page import ChatLongPressPage
from pages.collection.collection_page import CollectionPage
from core.logger_utils import logger
from strategy.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY


@allure.epic("IM核心功能测试")
@allure.feature("我的收藏-聊天页面收藏")
class TestChatCollection:
    """聊天页面发送收藏的测试类"""

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """
        每个测试用例开始前的初始化
        """
        self.mainPage = MainPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.longPressPage = ChatLongPressPage(driver_sender)
        self.collPage = CollectionPage(driver_sender)

        yield

        with allure.step("后置步骤：返回主页"):
            self.mainPage.go_to_main_page()

    def _enter_chat(self, strategy):
        """进入指定的聊天会话"""
        with allure.step(f"前置准备：进入会话 【{strategy.name}】"):
            self.chatListPage.enter_chat(strategy.name)

    @allure.step("聊天页面收藏一条消息通用断言")
    def common_first_assert(self, elem, msg_type):
        SUCCESS_MESSAGE = "成功"
        click_time = None
        try:
            # 执行长按
            self.longPressPage.long_press_action(elem)

            # 如果是图片，记录点击前的时间
            if msg_type == "image":
                click_time = self.chatPage.driver.get_device_time(format="YYYY/MM/DD HH:mm:ss")

            # 点击收藏
            self.longPressPage.click_favorite()

            # 获取 Toast 并断言
            alert_text = self.collPage.toast_message()
            logger.info(f"收藏结果: 期望结果：{SUCCESS_MESSAGE}, 实际结果：{alert_text}")
            check.equal(alert_text, SUCCESS_MESSAGE, msg=f"收藏失败，实际结果：{alert_text}")

            return click_time if alert_text == SUCCESS_MESSAGE else None
        except Exception as e:
            logger.error(f"❌ 收藏操作失败: {str(e)}")
            raise e

    @allure.step("进入我的收藏页面")
    def common_enter_my_collection(self):
        """进入我的收藏页面"""
        self.chatPage.back_to_chat_page()  # 先确保在聊天页
        self.chatPage.click_back_button()  # 返回到聊天列表页
        self.collPage.enter_my_collection()

    def _verify_text_collected(self, expected_data, is_list=False):
        """
        验证文本是否收藏成功
        :param expected_data: 预期的文本 (字符串 或 字符串列表)
        :param is_list: 是否验证多条数据
        """
        with allure.step(f"验证文本收藏结果: {'列表' if is_list else '单条'}"):
            if not is_list:
                actual_list = self.collPage.get_collection_text_data()
                assert actual_list, "收藏列表为空"
                assert expected_data == actual_list[0], \
                    f"首条数据不一致! 预期: {expected_data}, 实际: {actual_list[0]}"
            else:
                actual_list = self.collPage.get_collection_text_data(len(expected_data))
                logger.info(f"列表数据对比: 预期={expected_data}, 实际={actual_list}")
                assert expected_data == actual_list, \
                    f"列表数据不一致! 预期: {expected_data}, 实际: {actual_list}"

    def _verify_image_collected(self, expected_times):
        """
        验证图片是否收藏成功 (基于时间校验)
        :param expected_times: 预期时间字符串 (单个 str 或 list)
        """
        with allure.step("验证图片收藏结果(时间校验)"):
            if not isinstance(expected_times, list):
                expected_times = [expected_times]
            count = len(expected_times)
            details_list = self.collPage.get_collection_details_data('image', count if count > 1 else 0)
            logger.info(f"列表数据对比: 预期={expected_times}, 获取={details_list}")
            if isinstance(details_list, dict):
                details_list = [details_list]
            if count > 1:
                ui_times_str = self.collPage.get_sort_time(details_list)
            else:
                ui_times_str = [details_list[0]['collected_time']]
            assert len(ui_times_str) == len(expected_times), \
                f"数量不匹配! UI显示: {len(ui_times_str)}条, 预期: {len(expected_times)}条"

            for i, (exp_str, ui_str) in enumerate(zip(expected_times, ui_times_str)):
                exp_dt = self.collPage.str_to_dtime(exp_str)
                act_dt = self.collPage.str_to_dtime(ui_str)
                diff = abs((act_dt - exp_dt).total_seconds())
                logger.info(f"时间对比[{i}]: 预期={exp_str}, 实际={ui_str}, 误差={diff}s")
                assert diff <= 1.5, f"第{i + 1}条图片时间校验失败，误差 {diff}s > 1.5s"

    def _collect_first_available(self, msg_type: str):
        """
        [核心逻辑] 遍历发送方和接收方，收藏找到的第一条符合类型的消息
        :param msg_type: 'text' 或 'image'
        :return: 预期结果 (content 或 click_time)，如果未找到返回 None
        """
        search_sources = ["sent", "received"]
        for side in search_sources:
            elems = self.chatPage.get_message_elements(msg_type, side, expect_missing=True)
            if elems:
                elem = elems[0]
                content = elem.text if msg_type == "text" else ""
                logger.info(f"✅ 找到 {msg_type} 消息({side})，执行收藏...")
                res_time = self.common_first_assert(elem, msg_type)
                if msg_type == 'text':
                    return content
                else:
                    return res_time
        logger.warning(f"⚠️ 当前屏幕未找到任何 {msg_type} 消息")
        return None

    def _action_collect_visible_items(self, msg_type: str) -> list:
        """
        辅助函数：根据类型收藏当前页面所有发送/接收的消息
        :return: 收集到的预期数据列表
        """
        collected_data = []
        with allure.step(f"开始批量收藏当前页面的 {msg_type} 消息"):
            for direction in ["sent", "received"]:
                elems = self.chatPage.get_message_elements(msg_type, direction, expect_missing=True)
                if not elems:
                    logger.info(f"未找到 {direction} 方向的 {msg_type} 消息，跳过")
                    continue

                for index, elem in enumerate(elems):
                    try:
                        content = elem.text if msg_type == "text" else ""
                        result = self.common_first_assert(elem, msg_type)
                        # 收集预期结果
                        if msg_type == "text":
                            collected_data.append(content)
                        else:
                            if result is None:
                                logger.error(f"图片收藏断言必须返回时间，请检查 common_first_assert")
                                raise ValueError("图片收藏断言必须返回时间，请检查 common_first_assert")
                            collected_data.append(result)
                    except Exception as e:
                        logger.error(f"处理第 {index} 个元素失败: {e}")
                        raise e
        return collected_data

    def _verify_collection_result(self, msg_type: str, expected_data: list):
        """辅助函数：根据类型分发验证逻辑"""
        with allure.step("校验收藏列表数据"):
            if msg_type == "text":
                self._verify_text_collected(expected_data, True)
            elif msg_type == "image":
                self._verify_image_collected(expected_data)
            else:
                raise ValueError(f"未知的消息类型: {msg_type}")

    @allure.story("聊天页面收藏第一条(发送/接收)的文本消息")
    @allure.title("聊天页面收藏第一条({msg_source})的文本消息")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    @pytest.mark.parametrize("msg_source", ["sent", "received"], ids=["发送的文本消息", "接收的文本消息"])
    def test_collection_first_text(self, strategy, msg_source):
        self._enter_chat(strategy)

        elems = self.chatPage.get_message_elements("text", msg_source)
        assert elems, f"未找到 {msg_source} 的文本消息元素"
        elem = elems[0]
        text = elem.text

        self.common_first_assert(elem, "text")
        self.common_enter_my_collection()
        self._verify_text_collected(text, is_list=False)

    @allure.story("聊天页面收藏第一条(发送/接收)的图片消息")
    @allure.title("聊天页面收藏第一条({msg_source})的图片消息")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    @pytest.mark.parametrize("msg_source", ["sent", "received"], ids=["发送的图片消息", "接收的图片消息"])
    def test_collection_first_image(self, strategy, msg_source):
        self._enter_chat(strategy)

        elems = self.chatPage.get_message_elements("image", msg_source)
        assert elems, f"未找到 {msg_source} 的图片消息元素"
        elem = elems[0]

        coll_time = self.common_first_assert(elem, "image")
        self.common_enter_my_collection()
        self._verify_image_collected(coll_time)

    @allure.story("私聊聊天页面展示收藏所有(发送/接收)的文本消息")
    @allure.title("私聊聊天页面展示收藏所有({msg_source})的文本消息")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    @pytest.mark.parametrize("msg_source", ["sent", "received"], ids=["所有发送文本消息", "所有接收文本消息"])
    def test_collection_all_sent(self, strategy, msg_source):
        self._enter_chat(strategy)

        elems = self.chatPage.get_message_elements("text", msg_source)
        assert elems, f"未找到 {msg_source} 的文本消息元素"
        texts = [elem.text for elem in elems]

        for elem in elems:
            self.common_first_assert(elem, "text")
        self.common_enter_my_collection()
        expected_list = texts[::-1]  # 倒序
        self._verify_text_collected(expected_list, is_list=True)

    @allure.story("私聊聊天页面收藏展示的一条发送和接收文本消息")
    @allure.title("私聊聊天页面收藏展示的一条发送和接收文本消息")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_collection_one_sent_received_text(self, strategy):
        self._enter_chat(strategy)

        sent_elems = self.chatPage.get_message_elements("text", "sent")
        rece_elems = self.chatPage.get_message_elements("text", "received")
        assert sent_elems, "没有可用的已发送文本消息"
        assert rece_elems, "没有可用的已接收文本消息"

        sent_elem = sent_elems[0]
        received_elem = rece_elems[0]
        expected_texts = [received_elem.text, sent_elem.text]

        self.common_first_assert(sent_elem, "text")
        self.common_first_assert(received_elem, "text")
        self.common_enter_my_collection()
        self._verify_text_collected(expected_texts, True)

    @allure.story("私聊聊天页面收藏展示的一条发送和接收图片消息")
    @allure.title("私聊聊天页面收藏展示的一条发送和接收图片消息")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_collection_one_sent_received_image(self, strategy):
        self._enter_chat(strategy)

        sent_elems = self.chatPage.get_message_elements("image", "sent")
        rece_elems = self.chatPage.get_message_elements("image", "received")
        assert sent_elems, "没有可用的已发送图片消息"
        assert rece_elems, "没有可用的已接收图片消息"

        sent_elem = sent_elems[0]
        received_elem = rece_elems[0]

        sent_coll_time = self.common_first_assert(sent_elem, "image")
        rece_coll_time = self.common_first_assert(received_elem, "image")
        expected_times = [rece_coll_time, sent_coll_time]

        self.common_enter_my_collection()
        self._verify_image_collected(expected_times)

    @allure.story("私聊聊天页面收藏所有展示的文本消息(混合)")
    @allure.title("私聊聊天页面收藏所有展示的文本消息(混合)")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_collection_all_show_text(self, strategy):
        self._enter_chat(strategy)

        elems_s = self.chatPage.get_message_elements("text", "sent", expect_missing=True)
        texts_s = [elem.text for elem in elems_s]
        if elems_s:
            for elem in elems_s:
                self.common_first_assert(elem, "text")

        elems_r = self.chatPage.get_message_elements("text", "received", expect_missing=True)
        texts_r = [elem.text for elem in elems_r]
        if elems_r:
            for elem in elems_r:
                self.common_first_assert(elem, "text")

        expected_texts = texts_r[::-1] + texts_s[::-1]
        self.common_enter_my_collection()
        self._verify_text_collected(expected_texts, True)

    @allure.story("私聊聊天页面收藏所有展示的图片消息(混合)")
    @allure.title("私聊聊天页面收藏所有展示的图片消息(混合)")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_collection_all_show_image(self, strategy):
        self._enter_chat(strategy)

        elems_s = self.chatPage.get_message_elements("image", "sent", expect_missing=True)
        sent_times = []
        if elems_s:
            for elem in elems_s:
                st = self.common_first_assert(elem, "image")
                sent_times.append(st)

        elems_r = self.chatPage.get_message_elements("image", "received", expect_missing=True)
        rece_times = []
        if elems_r:
            for elem in elems_r:
                rt = self.common_first_assert(elem, "image")
                rece_times.append(rt)

        expected_times = rece_times[::-1] + sent_times[::-1]
        self.common_enter_my_collection()
        self._verify_image_collected(expected_times)

    @allure.story("私聊聊天页面收藏展示的一张图片和一条消息(混合场景)")
    @allure.title("私聊聊天页面收藏展示的一张图片和一条消息(混合场景)")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_collection_one_show_text_image(self, strategy):
        self._enter_chat(strategy)

        expected_text = self._collect_first_available("text")
        expected_time = self._collect_first_available("image")

        if not expected_text and not expected_time:
            pytest.skip("当前页面既无文本也无图片，跳过测试")

        self.common_enter_my_collection()
        if expected_time:
            self._verify_image_collected(expected_time)
        if expected_text:
            self._verify_text_collected(expected_text)

    @allure.story("私聊聊天页面收藏所有展示的(文本/图片)消息（混合）")
    @allure.title("私聊聊天页面收藏所有展示的({msg_type})消息")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    @pytest.mark.parametrize("msg_type", ["text", "image"], ids=["批量收藏文本", "批量收藏图片"])
    def test_collection_all_show_items(self, strategy, msg_type):
        self._enter_chat(strategy)

        expected_data = self._action_collect_visible_items(msg_type)
        if not expected_data:
            pytest.skip(f"当前页面没有 {msg_type} 类型的消息，跳过测试")

        self.common_enter_my_collection()
        final_expected = expected_data[::-1]
        self._verify_collection_result(msg_type, final_expected)
