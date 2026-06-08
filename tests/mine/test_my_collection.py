import allure
import pytest
import pytest_check as check
from pytest_check import equal

from pages.main.main_page import MainPage
from pages.mine.collection_page import CollectionPage
from core.logger_utils import logger


@pytest.mark.usefixtures('message_page')
@allure.epic("IM核心功能测试")
@allure.feature("我的模块-收藏夹")
@allure.story("进入我的收藏页面")
class TestCollection:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        """
        每个测试类开始前，自动获取 self.collPage 实例并绑定到 self
        这样下面的方法就不需要反复传参了
        """
        self.collPage = CollectionPage(driver_sender)
        self.mainPage = MainPage(driver_sender)

    """ 执行测试函数前需要构造数据 """

    # 收藏第一条消息通用断言
    @allure.step("私聊聊天页面收藏一条消息通用断言")
    def common_first_assert(self, elem, msg_type):
        SUCCESS_MESSAGE = "成功"
        ERROR_MESSAGE_TYPE = "消息类型错误"
        click_time = None
        try:
            # 点击收藏
            if msg_type == "text":
                self.collPage.click_collection(elem)
            elif msg_type == "image":
                click_time = self.collPage.get_first_collection_item(elem)
                # self.collPage.get_received_image_screenshot()
            else:
                raise Exception(ERROR_MESSAGE_TYPE)
            alert_text = self.collPage.toast_message()
            logger.info(f"收藏结果: 期望结果：{SUCCESS_MESSAGE}, 实际结果：{alert_text}")
            # assert alert_text == SUCCESS_MESSAGE, f"收藏失败，实际结果：{alert_text}"
            check.equal(alert_text, SUCCESS_MESSAGE, msg=f"收藏失败，实际结果：{alert_text}")
            return click_time if equal(alert_text, SUCCESS_MESSAGE) else None
        except AttributeError as e:
            raise AttributeError(f"页面元素操作异常: {str(e)}")
        except Exception as e:
            raise Exception(f"收藏操作失败: {str(e)}")

    @allure.step("进入我的收藏页面")
    def common_enter_my_collection(self):
        """ 进入我的收藏页面 """
        with allure.step("进入我的收藏页面"):
            self.collPage.back_to_main()
            self.collPage.enter_my_collection()

    @allure.step("回到消息页面")
    def common_go_to_message_page(self):
        self.collPage.back()
        self.mainPage.go_to_message_page()

    def _verify_text_collected(self, expected_data, is_list=False):
        """
        验证文本是否收藏成功
        :param expected_data: 预期的文本 (字符串 或 字符串列表)
        :param is_list: 是否验证多条数据
        """
        with allure.step(f"验证文本收藏结果: {'列表' if is_list else '单条'}"):
            if not is_list:
                # 验证单条：获取列表第一条对比
                actual_list = self.collPage.get_collection_text_data()
                assert actual_list, "收藏列表为空"
                assert expected_data == actual_list[0], \
                    f"首条数据不一致! 预期: {expected_data}, 实际: {actual_list[0]}"
            else:
                # 验证多条：获取指定数量对比
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
            # 统一转为列表处理
            if not isinstance(expected_times, list):
                expected_times = [expected_times]
            count = len(expected_times)
            # 获取 UI 上的详情数据
            details_list = self.collPage.get_collection_details_data('image', count if count > 1 else 0)
            logger.info(f"列表数据对比: 预期={expected_times}, 获取={details_list}")
            # 如果是单条，get_collection_details_data 可能返回 dict，需兼容处理
            if isinstance(details_list, dict):
                details_list = [details_list]
            # 提取 UI 时间
            if count > 1:
                ui_times_str = self.collPage.get_sort_time(details_list)
            else:
                ui_times_str = [details_list[0]['collected_time']]
            assert len(ui_times_str) == len(expected_times), \
                f"数量不匹配! UI显示: {len(ui_times_str)}条, 预期: {len(expected_times)}条"

            for i, (exp_str, ui_str) in enumerate(zip(expected_times, ui_times_str)):
                # 时间转换
                exp_dt = self.collPage.str_to_dtime(exp_str)
                act_dt = self.collPage.str_to_dtime(ui_str)
                # 计算误差 <= 1.0 秒  注意：这里推荐用 <= 1.5 或 2.0，因为网络请求很难在 1秒内完成落库
                diff = abs((act_dt - exp_dt).total_seconds())
                logger.info(f"时间对比[{i}]: 预期={exp_str}, 实际={ui_str}, 误差={diff}s")
                print(f"时间对比[{i}]: 预期={exp_str}, 实际={ui_str}, 误差={diff}s")
                assert diff <= 1.5, f"第{i + 1}条图片时间校验失败，误差 {diff}s > 1.5s"

    def _collect_first_available(self, msg_type: str):
        """
        [核心逻辑] 遍历发送方和接收方，收藏找到的第一条符合类型的消息
        :param msg_type: 'text' 或 'image'
        :return: 预期结果 (content 或 click_time)，如果未找到返回 None
        """
        # 定义查找源顺序：先找发送方，再找接收方 (顺序可调)    只取第1条 (index=0)
        search_sources = [
            (self.collPage.get_sent_text if msg_type == "text" else self.collPage.get_sent_image),
            (self.collPage.get_received_text if msg_type == "text" else self.collPage.get_received_image)
        ]

        for get_method in search_sources:
            # 尝试获取单条数据 (index=0)
            elem, content = get_method(0, False)

            if elem:
                logger.info(f"✅ 找到 {msg_type} 消息，执行收藏... {content}")
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
        # 策略配置 A: 元素获取方法的映射 结构: type -> direction -> method 放在方法里或类属性里，不要污染测试用例
        strategies = {
            "text": {
                "sent": self.collPage.get_sent_text,
                "received": self.collPage.get_received_text
            },
            "image": {
                "sent": self.collPage.get_sent_image,
                "received": self.collPage.get_received_image
            }
        }
        collected_data = []
        with allure.step(f"开始批量收藏当前页面的 {msg_type} 消息"):
            for direction in ["sent", "received"]:
                get_method = strategies[msg_type][direction]

                # 获取元素
                elems, content_list = get_method(1, True)
                if not elems:
                    logger.info(f"未找到 {direction} 方向的 {msg_type} 消息，跳过")
                    continue

                # --- ⚠️ 风险区域 ---
                # 如果 common_first_assert 导致页面刷新，下面的循环会报错
                for index, (elem, content) in enumerate(zip(elems, content_list)):
                    try:
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

    @allure.step("时间校验")
    def _assert_time_diff(self, dt1, dt2, threshold: int = 1.5):
        """辅助方法：断言两个时间对象的差值"""
        diff = abs((dt1 - dt2).total_seconds())
        # 误差 <= 1.0 秒  注意：这里推荐用 <= 1.5 或 2.0，因为网络请求很难在 1秒内完成落库
        assert diff <= threshold, (f"❌ 时间校验失败！误差 {diff}s 超过了 {threshold}s 限制。"
                                   f"操作时间: {dt2}"
                                   f"UI显示: {dt1}")

    @allure.story("私聊聊天页面收藏第一条(发送/接收)的文本消息")
    @pytest.mark.parametrize("msg_source", ["sent", "received"], ids=["发送的文本消息", "接收的文本消息"])
    def test_collection_first_text(self, msg_source):
        # 进入第一个对话框
        self.collPage.click_enter_first_content()
        # 获取消息
        if msg_source == "sent":
            elem, text = self.collPage.get_sent_text()
        else:
            elem, text = self.collPage.get_received_text()
        self.common_first_assert(elem, "text")
        self.common_enter_my_collection()
        self._verify_text_collected(text, is_list=False)
        self.common_go_to_message_page()

    @allure.story("私聊聊天页面收藏第一条(发送/接收)的图片消息")
    @pytest.mark.parametrize("msg_source", ["sent", "received"], ids=["发送的图片消息", "接收的图片消息"])
    def test_collection_first_image(self, msg_source):
        # 进入第一个对话框
        self.collPage.click_enter_first_content()
        # 获取消息
        if msg_source == "sent":
            elem, image = self.collPage.get_sent_image()
        else:
            elem, image = self.collPage.get_received_image()
        coll_time = self.common_first_assert(elem, "image")
        self.common_enter_my_collection()
        self._verify_image_collected(coll_time)
        self.common_go_to_message_page()

    @allure.story("私聊聊天页面展示收藏所有(发送/接收)的文本消息")
    @pytest.mark.parametrize("msg_source", ["sent", "received"], ids=["所有发送文本消息", "所有接收文本消息"])
    def test_collection_all_sent(self, msg_source):
        # 进入第一个对话框
        self.collPage.click_enter_first_content()
        textC = self.collPage.get_sent_text_count()  # 获取消息数量
        # 获取所有消息
        if msg_source == "sent":
            elems, texts = self.collPage.get_sent_text(textC, True)
        else:
            elems, texts = self.collPage.get_received_text(textC, True)
        for elem in elems:
            self.common_first_assert(elem, "text")
        self.common_enter_my_collection()
        expected_list = texts[::-1]  # 倒序
        self._verify_text_collected(expected_list, is_list=True)
        self.common_go_to_message_page()
        self.collPage.back()

    @allure.story("私聊聊天页面收藏展示的一条发送和接收文本消息")
    def test_collection_one_sent_received_text(self):
        # 进入第一个对话框
        self.collPage.click_enter_first_content()
        # 获取第一条发送消息
        sent_elem, sent_text = self.collPage.get_sent_text()
        # 获取第一条接收消息
        received_elem, received_text = self.collPage.get_received_text()
        expected_texts = [received_text, sent_text]
        self.common_first_assert(sent_elem, "text")
        self.common_first_assert(received_elem, "text")
        self.common_enter_my_collection()
        self._verify_text_collected(expected_texts, True)
        self.common_go_to_message_page()
        self.collPage.back()

    @allure.story("私聊聊天页面收藏展示的一条发送和接收图片消息")
    def test_collection_one_sent_received_image(self):
        self.collPage.click_enter_first_content()
        sent_elem, sent_img = self.collPage.get_sent_image()
        received_elem, received_img = self.collPage.get_received_image()
        sent_coll_time = self.common_first_assert(sent_elem, "image")
        rece_coll_time = self.common_first_assert(received_elem, "image")
        expected_times = [sent_coll_time, rece_coll_time]  # 预期时间列表
        self.common_enter_my_collection()
        self._verify_image_collected(expected_times)
        self.common_go_to_message_page()
        self.collPage.back()

    @allure.story("私聊聊天页面收藏所有展示的文本消息(混合)")
    def test_collection_all_show_text(self):
        # 进入第一个对话框
        self.collPage.click_enter_first_content()
        # 获取所有发送消息
        elems_s, texts_s = self.collPage.get_sent_text(1, True)
        if elems_s:
            for elem, sent_text in zip(elems_s, texts_s):
                self.common_first_assert(elem, "text")
        # 获取所有接收消息
        elems_r, texts_r = self.collPage.get_received_text(1, True)
        if elems_r:
            for elem, received_text in zip(elems_r, texts_r):
                self.common_first_assert(elem, "text")
        # 构造预期结果 (后收藏的在前：接收倒序 + 发送倒序)
        expected_texts = texts_s[::-1] + texts_r[::-1]
        self.common_enter_my_collection()
        self._verify_text_collected(expected_texts, True)
        self.common_go_to_message_page()
        self.collPage.back()

    @allure.story("待验证")
    @allure.story("私聊聊天页面收藏所有展示的图片消息(混合)")
    def test_collection_all_show_image(self):
        self.collPage.click_enter_first_content()
        # 处理发送的图片
        elems_s, imgs_s = self.collPage.get_sent_image(1, True)
        sent_times = []
        if elems_s:
            for elem, sent_text in zip(elems_s, imgs_s):
                st = self.common_first_assert(elem, "image")
                sent_times.append(st)
        # 处理接收的图片
        elems_s, imgs_r = self.collPage.get_received_image(1, True)
        rece_times = []
        if elems_s:
            for elem, received_text in zip(elems_s, imgs_r):
                rt = self.common_first_assert(elem, "image")
                rece_times.append(rt)
        # 构造预期结果 (后收藏的在前：接收倒序 + 发送倒序)
        expected_texts = imgs_s[::-1] + imgs_r[::-1]
        self.common_enter_my_collection()
        self._verify_text_collected(expected_texts, True)
        self.common_go_to_message_page()  # 返回
        self.collPage.back()

    @allure.story("待验证")
    @allure.story("私聊聊天页面收藏展示的一张图片和一条消息(混合场景)")
    def test_collection_one_show_text_image(self):
        self.collPage.click_enter_first_content()
        expected_text = self._collect_first_available("text")
        expected_time = self._collect_first_available("image")

        if not expected_text and not expected_time:
            pytest.skip("当前页面既无文本也无图片，跳过测试")

        self.common_enter_my_collection()
        if expected_time:
            self._verify_image_collected(expected_time)
        if expected_text:
            self._verify_text_collected(expected_text)
        self.collPage.back()
        self.mainPage.go_to_message_page()

    @allure.story("待验证")
    @allure.story("私聊聊天页面收藏所有展示的(文本/图片)消息（混合）")
    @pytest.mark.parametrize("msg_type", ["text", "image"], ids=["批量收藏文本", "批量收藏图片"])
    def test_collection_all_show_items(self, msg_type):
        """
        通用测试用例：获取当前屏幕所有发送和接收的消息(文本或图片)，全部收藏，并校验列表
        """
        self.collPage.click_enter_first_content()

        # 策略配置 A: 元素获取方法的映射 结构: type -> direction -> method
        expected_data = self._action_collect_visible_items(msg_type)

        # 检查是否收集到了数据
        if not expected_data:
            self.collPage.back()
            logger.warning(f"未找到 coll_expected = {expected_data} 消息")
            pytest.skip(f"当前页面没有 {msg_type} 类型的消息，跳过测试")

        self.common_enter_my_collection()

        final_expected = expected_data[::-1]
        logger.info(f"预期结果列表：(共){len(final_expected)}) 消息: {final_expected}")

        # 7. 执行策略断言
        self._verify_collection_result(msg_type, final_expected)

        # 恢复环境
        self.collPage.back()
        self.mainPage.go_to_message_page()

    @allure.story("朋友圈页面收藏文本消息")
    def test_collection_friend_text(self):
        pass

    @allure.story("朋友圈页面收藏图片消息")
    def test_collection_friend_image(self):
        pass

    @allure.story("收藏中当前页面分享第一条文本消息")
    def test_share_first_text(self):
        pass

    @allure.story("收藏中当前页面随机分享一条文本消息")
    def test_share_random_text(self):
        pass

    @allure.story("收藏中当前页面分享第一张图片消息")
    def test_share_first_image(self):
        pass

    @allure.story("收藏中当前页面随机分享一张图片消息")
    def test_share_random_image(self):
        pass

    @allure.story("收藏中分享最后一条文本消息")
    def test_share_last_text(self):
        pass

    @allure.story("收藏中分享最后一张图片消息")
    def test_share_last_image(self):
        pass

    @allure.story("我的收藏中删除元素最新一条(文本/图片)")
    @pytest.mark.parametrize("item_type", ["text", "image"], ids=["删除最新文本", "删除最新图片"])
    def test_delete_collection_first_item(self, item_type):
        self.collPage.enter_my_collection()
        # 1. 获取删除前的数据
        data_pre = self.collPage.get_collection_details_data(item_type, index=0)
        # 2. 执行删除
        self.collPage.del_collection_item(item_type, 0)
        # 3. 获取删除后的数据并校验
        data_after = self.collPage.get_collection_details_data(item_type, index=0)
        print(f" data_pre = {data_pre}, data_after = {data_after} ")
        self.collPage.back()

        if not data_after or not data_pre:
            # 场景 A: 删除了唯一的一条数据，现在列表里没有该类型数据了
            logger.info("✅  删除成功 (列表已无该类型数据) 或 没有找到该数据")
            assert True, f"删除失败 (已无该类型数据)"
        else:
            # 场景 B: 还有其他数据，原来的第二条变成了第一条
            assert data_pre['collected_time'] != data_after['collected_time'], \
                f"删除失败: 首条数据时间戳未变化 ({data_pre['collected_time']})"

    @allure.story("我的收藏中删除元素所有(文本/图片)收藏")
    @pytest.mark.parametrize("item_type", ["text", "image"], ids=["删除所有文本", "删除所有图片"])
    def test_delete_collection_texts(self, item_type):
        self.collPage.enter_my_collection()
        del_item = self.collPage.del_collection_item(item_type, 1)
        self.collPage.back()
        assert del_item == 0, f'还有 {del_item} 条 {item_type} 数据未删除'

    @allure.story("我的收藏中删除所有元素收藏")
    def test_delete_collection_all(self, item_type: str = "all"):
        self.collPage.enter_my_collection()
        del_item = self.collPage.del_collection_item("all", 1)
        self.collPage.back()
        assert del_item == 0, f'还有 {del_item} 条 {item_type} 数据未删除'

    @allure.story("test")
    @allure.story("上滑收藏")
    def test_swipe_collection(self):
        # 进入第一个对话框
        self.collPage.click_enter_first_content()
        while (True):
            # 获取所有发送消息
            elems, texts_r = self.collPage.get_sent_text(1, True)
            if len(elems) > 0 and len(texts_r) > 0:
                for elem, sent_text in zip(elems, texts_r):
                    self.common_first_assert(elem, "text")
            elems, imgs_r = self.collPage.get_sent_image(1, True)
            if len(elems) > 0 and len(imgs_r) > 0:
                for elem, sent_img in zip(elems, imgs_r):
                    self.common_first_assert(elem, "image")
            self.collPage.swipe_page_quickly(duration=100, max_swipes=1)
