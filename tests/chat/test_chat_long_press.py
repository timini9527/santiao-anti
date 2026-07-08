import time
import pytest
import allure
import pytest_check as check
from pages.system.main.main_page import MainPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.core.chat_long_press_page import ChatLongPressPage
from core.logger_utils import logger
from strategy.chat.chat_strategy import PRIVATE_USER1, GROUP_STRATEGY
from strategy.chat.chat_message_strategy import MessageTypeStrategy, ChatMessageBuilder
from locators.chat.core.chat_locator import ChatLocator
from pages.system.home.side_slip_page import SideSlipPage
from pages.system.home.home_page import HomePage
from pages.personal.collection.chat_collection_page import ChatCollectionPage
from pages.system.common.contact_select_page import ContactSelectPage
from pages.system.common.session_select_page import SessionSelectPage
from pages.chat.chat_options.emojis.chat_emoji_package_page import ChatEmojiPackagePage




@allure.epic("IM核心功能测试")
@allure.feature("聊天模块-长按菜单")
class TestChatLongPress:

    @pytest.fixture(autouse=True)
    def setup(self, driver_sender):
        self.mainPage = MainPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.longPressPage = ChatLongPressPage(driver_sender)
        self.messageBuilder = ChatMessageBuilder(driver_sender)
        self.collectionPage = ChatCollectionPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.sideSlipPage = SideSlipPage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        self.sessionSelectPage = SessionSelectPage(driver_sender)
        self.emojiPackagePage = ChatEmojiPackagePage(driver_sender)

        yield

        with allure.step("后置步骤：返回主页"):
            self.mainPage.go_to_main_page()


    def _prepare_message(self, msg_type: str):
        """辅助方法：在当前会话中发送待测消息"""
        self.messageBuilder.build_message(msg_type)
        is_sent = self.chatPage.wait_for_last_message_send_status()
        check.is_true(is_sent, f"❌ 消息【{msg_type}】未能成功发送上屏 或 发送失败")


    @allure.story("不同消息长按菜单的完整性校验")
    @allure.title("不同消息长按菜单的完整性校验-状态：已完成")
    @pytest.mark.parametrize("msg_type", ["text", "voice", "image", "video", "position", "card", "file", "package"])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_long_press_display_action(self, strategy, msg_type):

        with allure.step(f"1. 前置准备：进入聊天页面并发送一条【{msg_type}】消息"):
            self.chatListPage.enter_chat(strategy.name)
            self.chatPage.send_message(f"【{msg_type}】长按菜单的完整性校验")
            self.messageBuilder.build_message(msg_type)
            
        with allure.step("2. 结果验证：确保消息已成功上屏"):
            is_sent = self.chatPage.wait_for_last_message_send_status()
            check.is_true(is_sent, f"❌ 消息【{msg_type}】未能成功发送上屏 或 发送失败")
                
        with allure.step("3. 执行操作：长按最后一条消息"):
            self.longPressPage.long_press_last_message()
        
        with allure.step(f"4. 校验【{msg_type}】长按菜单项"):
            is_items_ok = self.longPressPage.get_menu_items(msg_type, is_admin=strategy.is_admin)
            check.is_true(is_items_ok, f"❌ 消息【{msg_type}】长按菜单项未识别")


    @allure.story("长按菜单操作专项：复制")
    @allure.title("长按菜单操作专项：复制-状态：已完成")
    @pytest.mark.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("msg_type", ["text", "emoji", "image", "voice", "video", "position", "card", "file", "package"])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_long_press_action_copy(self, strategy, msg_type):
        
        with allure.step(f"1. 进入聊天页面"):
            self.chatListPage.enter_chat(strategy.name)
            # self.chatPage.send_message(f"【{msg_type}】长按复制功能专项")

        # 校验消息是否支持复制
        with allure.step(f"2. 校验【{msg_type}】长按菜单项"):
            strategy_model = MessageTypeStrategy.get_strategy(msg_type)
            if "复制" not in strategy_model.expected_menus:
                pytest.skip(f"⏭️ {msg_type} 消息类型不支持【复制】，自动跳过")
                
        with allure.step(f"3. 前置准备：进入聊天页面并发送一条【{msg_type}】消息"):
            self._prepare_message(msg_type)

        with allure.step("4. 执行操作：长按并点击【复制】"):
            self.longPressPage.long_press_last_message()
            is_ok = self.longPressPage._execute_and_verify_menu_item("复制")
            check.is_true(is_ok, "❌ 长按点击【复制】失败")

        with allure.step("5. 结果验证：验证复制内容"):
            if msg_type == "text":
                expected_text = "发送收藏消息进行测试‼️⚠️🚀✔️✅♏🧑‍🚀🪲🍎✖️"
                paste_text = self.chatPage.paste_clipboard_text()
                check.equal(paste_text, expected_text, f"❌ 复制内容不一致: {paste_text}")
            elif msg_type == "emoji":
                expected_text = self.chatPage.get_text_message_content_by_index(index=-1)
                # expected_text = "[下雨][不要][书呆子][亲亲][伤心][做鬼脸][偷笑][兔子][冰棍][删除][可怜][可爱][吃惊][吐][呵呵][咖啡][哈哈][哼][嘘][嘻嘻][囧][困][围观][大笑][太开心][太阳][失望][奥特曼][好][委屈][威武][实习][害羞][帅][干杯][弱][心][怒][怒骂][思考][悲伤][感冒][愤怒][手机][打哈欠][抓狂][抠鼻屎][拜拜][拳头][握手][晕][最差][月亮][来][汗][汽车][沙尘暴][没问题][浮云][照相机][熊猫][爱你][爱心传递][猪头][生病][电影][疑问][睡觉][礼物][神马][累][给力][耶][花心][萌][蛋糕][衰][西瓜][话筒][赞][足球][鄙视][酷][钟][钱][链接危险][链接安全][链接未知][链接警告][闭嘴][阴险][音乐][顶][风扇][飞机][馋嘴][鲜花][黑线][鼓掌]"
                paste_text = self.chatPage.paste_clipboard_text()
                check.equal(expected_text, paste_text, f"❌ 复制内容不一致: {paste_text}")
                

    @allure.story("长按菜单操作专项：收藏")
    @allure.title("长按菜单操作专项：收藏-状态：已完成")
    @pytest.mark.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("msg_type", ["text", "emoji", "image", "voice", "video", "position", "card", "file", "package"])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_long_press_action_collection(self, strategy, msg_type):
        
        with allure.step(f"1. 进入聊天页面"):
            self.chatListPage.enter_chat(strategy.name)
            # self.chatPage.send_message(f"【{msg_type}】长按【收藏】功能专项")

        with allure.step(f"2. 校验【{msg_type}】长按菜单项"):
            strategy_model = MessageTypeStrategy.get_strategy(msg_type)
            if "收藏" not in strategy_model.expected_menus:
                pytest.skip(f"⏭️ {msg_type} 消息类型不支持【收藏】，自动跳过")

        with allure.step(f"3. 前置准备：进入聊天页面并发送一条【{msg_type}】消息"):
            self._prepare_message(msg_type)

        with allure.step(f"4. 记录【{msg_type}】消息原始特征数据"):
            original_hash = None
            if msg_type == "image":
                original_hash = self.chatPage.get_chat_image_hash(index=-1)
                check.is_true(original_hash, "❌ 图片消息原始 hash 获取失败")

        with allure.step(f"5. 【{msg_type}】执行长按并点击【收藏】"):
            self.longPressPage.long_press_last_message()
            is_ok = self.longPressPage._execute_and_verify_menu_item("收藏")
            check.is_true(is_ok, "❌ 长按点击【收藏】失败")

        with allure.step(f"6. 【{msg_type}】跨页面比对：前往收藏夹验证数据"):
            self.mainPage.go_to_main_page()
            self.homePage.open_left_menu()
            self.sideSlipPage.click_collection()

            expected_text = "发送收藏消息进行测试‼️⚠️🚀✔️✅♏🧑‍🚀🪲🍎✖️"
            if msg_type == "text":
                coll_tt = self.collectionPage.get_collection_text_content()
                check.equal(coll_tt, expected_text, f"❌ 收藏夹文本不一致: {coll_tt}")
            elif msg_type == "image":
                coll_img_hash = self.collectionPage.get_collection_image_hash()
                is_similar = self.collectionPage.verify_image_similarity(hash1=coll_img_hash, hash2=original_hash, threshold=100)
                check.is_true(is_similar, f"❌ 收藏夹图片不一致: 列表hash:{coll_img_hash}, 发送hash: {original_hash}")


    @allure.story("长按菜单操作专项：转发")
    @allure.title("长按菜单操作专项：转发-状态：已完成")
    @pytest.mark.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("msg_type", ["text", "emoji", "image", "package", "video", "position", "card", "file", "voice"])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_long_press_action_forward(self, strategy, msg_type):

        with allure.step(f"1. 进入聊天页面"):
            self.chatListPage.enter_chat(strategy.name)
            # self.chatPage.send_message(f"【{msg_type}】长按【转发】功能专项")
            
        with allure.step(f"2. 校验【{msg_type}】长按菜单项"):
            strategy_model = MessageTypeStrategy.get_strategy(msg_type)
            if "转发" not in strategy_model.expected_menus:
                pytest.skip(f"⏭️ {msg_type} 消息类型不支持【转发】，自动跳过")

        with allure.step(f"3. 前置准备：进入聊天页面并发送一条【{msg_type}】消息"):
            self._prepare_message(msg_type)


        with allure.step("4. 预存原始数据"):
            pre_data = self.messageBuilder.get_message_feature(msg_type)
            if msg_type == "file":
                check.is_in("发送成功", pre_data.get("文件状态", ""), f"❌ 文件消息发送失败")

        with allure.step("5. 执行长按并点击【转发】"):
            self.longPressPage.long_press_last_message()
            msg_type_num = 1 if msg_type == "image" else 0
            is_ok = self.longPressPage._execute_and_verify_menu_item("转发", msg_type=msg_type_num)
            check.is_true(is_ok, "❌ 长按点击【转发】失败")

        with allure.step(f"6. 选择好友【{strategy.name}】进行转发"):
            is_select = self.contactSelectPage.forward_select_contact_by_name(name=strategy.name, msg_type=msg_type_num)
            check.is_true(is_select, f"❌ 未能选择转发对象: {strategy.name}")
            self.sessionSelectPage.click_finish_button(msg_type=msg_type_num)
            self.chatPage.wait_for_last_message_send_status()

            # 统一提取转发后的特征值
            re_data = self.messageBuilder.get_message_feature(msg_type)
            
            # 断言逻辑归一化
            if msg_type == "package":
                is_similar = self.emojiPackagePage.compare_emoji_hashcode(re_data["表情哈希"], pre_data["表情哈希"])
                check.is_true(is_similar, f"❌ 转发表情内容不一致")
            elif msg_type == "file":
                check.equal(re_data["文件名"], pre_data["文件名"], f"❌ 转发文件名不一致")
                # check.equal(re_data["文件大小"], pre_data["文件大小"], f"❌ 转发文件大小不一致")
                check.is_in("发送成功", re_data["文件状态"], f"❌ 文件消息转发失败，状态为{re_data['文件状态']}")
            else:
                # 对常规属性执行自动化字典对齐校验
                for key, expected_val in pre_data.items():
                    actual_val = re_data.get(key)
                    check.equal(actual_val, expected_val, f"❌ 转发 {key} 不一致: 期望 '{expected_val}', 实际 '{actual_val}'")


    @allure.story("长按菜单操作专项：多选")
    @allure.title("长按菜单操作专项：多选-状态：已完成")
    @pytest.mark.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("msg_list", [
        ["text", "emoji", "image", "voice", "video", "position", "card", "file", "package"]
    ], ids=["全量消息类型"])
    @pytest.mark.parametrize("msg_count", [None, 100, 101], ids=["跟随列表长度", "选100个边界", "超限101个"])
    @pytest.mark.parametrize("mult_type", [0, 1], ids=lambda x: "逐条转发" if x == 0 else "合并转发")
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_long_press_action_multi_select(self, strategy, mult_type, msg_list, msg_count):
        allure.dynamic.title(f"【多选专项】 {strategy.desc} - 类型 {mult_type}")
        
        with allure.step(f"1. 进入聊天页面"):
            self.chatListPage.enter_chat(strategy.name)
            self.chatPage.send_message(f"【{msg_list}】长按【多选】功能专项")

        with allure.step(f"2. 【多选】 验证消息类型，准备多条不同消息"):
            if msg_count is None:
                target_count = len(msg_list)
                for msg_type in msg_list:
                    strategy_model = MessageTypeStrategy.get_strategy(msg_type)
                    if "多选" not in strategy_model.expected_menus:
                        continue
                    self._prepare_message(msg_type)

                    # self.chatPage.click_back_button()
            else:
                target_count = msg_count

        with allure.step(f"3. 长按执行【多选】"):
            self.longPressPage.long_press_last_message()
            is_ok = self.longPressPage._execute_and_verify_menu_item("多选")
            check.is_true(is_ok, f"❌ 长按点击【多选】执行失败")
        
        with allure.step("4. 勾选多条消息"):
            multi_seleced_count = self.longPressPage.click_x_select_checkbox_buttons(target_count=target_count)
            if target_count <= 100:
                check.equal(multi_seleced_count, target_count, f"❌ 勾选多条消息失败，实际勾选数量为 {multi_seleced_count}")
            else:
                is_toast_caught = isinstance(multi_seleced_count, str) and "100" in multi_seleced_count
                check.is_true(is_toast_caught, f"❌ 超限拦截失败，预期应弹窗拦截，实际返回为 {multi_seleced_count}")
                # 超限异常场景只为了测试阻断机制，断言通过后直接退出用例，不走后续转发流程
                return

        with allure.step("5. 勾选消息后，点击【转发】按钮"):
            if mult_type == 0 and target_count <= 10:
                self.longPressPage.click_forward_button()
                self.longPressPage.click_batch_forward_button()
            elif mult_type == 1:
                self.longPressPage.click_forward_button()
                self.longPressPage.click_merge_forward_button()
            else:
                # self.chatListPage.click_cancel_button()
                self.chatPage.click_cancel_send_button()
                return
        
        with allure.step(f"6. 选择好友【{strategy.name}】进行转发"):
            is_select = self.contactSelectPage.forward_select_contact_by_name(name=strategy.name)
            check.is_true(is_select, f"❌ 未能选择转发对象: {strategy.name}")
            self.sessionSelectPage.click_finish_button()
            self.chatPage.wait_for_history_send_complete()
            self.chatPage.wait_for_last_message_send_status()

        with allure.step(f"7. 验证【{'逐条转发' if mult_type == 0 else '合并转发'}】后的消息"):
            is_sent = self.chatPage.wait_for_last_message_send_status()
            check.is_true(is_sent, f"❌ {'逐条转发' if mult_type == 0 else '合并转发'}后，末尾消息发送失败或未上屏")

            if mult_type == 0 and target_count <= 10:
                last_msg_type = msg_list[-1]
                if last_msg_type == "package":
                    is_rendered = self.emojiPackagePage.verify_emoji_message_rendered()
                    check.is_true(is_rendered, f"❌ {'逐条转发'}的最后一条不是预期的 Package 动态表情")
            elif mult_type == 1:
                forward_title = self.chatPage.get_merge_forward_message()
                check.is_in("聊天记录", forward_title, f"❌ 合并转发后，末尾消息不是聊天记录消息")

                with allure.step("7. 穿透验证：解析合并转发预览文本与防 Crash 验证"):
                    is_history_correct = self.chatPage.verify_chat_history_content(expected_count=target_count)
                    check.is_true(is_history_correct, f"❌ 合并转发验证失败（预览条数不匹配或详情页崩溃）")
            else:
                pass

    
    @allure.story("长按菜单操作专项：添加表情")
    @allure.title("长按菜单操作专项：添加表情-状态：已完成")
    @pytest.mark.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("msg_type", ["text", "emoji", "image", "package", "video", "position", "card", "file", "voice"])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_long_press_action_add_emoji(self, strategy, msg_type):
        
        with allure.step(f"1. 进入聊天页面"):
            self.chatListPage.enter_chat(strategy.name)
            self.chatPage.send_message(f"【{msg_type}】长按【添加表情】功能专项")

        with allure.step(f"2. 校验【{msg_type}】长按菜单项"):
            strategy_model = MessageTypeStrategy.get_strategy(msg_type)
            if "添加表情" not in strategy_model.expected_menus:
                pytest.skip(f"⏭️ {msg_type} 消息类型不支持【添加表情】，自动跳过")
        
        with allure.step("3. 前置准备：移除全部已添加的表情包"):
            is_revoked = self.messageBuilder._prepare_collection_emoji_msg()
            check.is_true(is_revoked, f"❌ 表情包移除失败")

        with allure.step(f"4. 前置准备：进入聊天页面并发送一条【{msg_type}】消息"):
            self._prepare_message(msg_type)


        with allure.step(f"5. 执行长按并点击【添加表情】"):
            self.longPressPage.long_press_last_message()
            is_ok = self.longPressPage._execute_and_verify_menu_item("添加表情")
            check.is_true(is_ok, "❌ 长按点击【添加表情】失败")

        with allure.step(f"6. 结果验证：验证添加表情效果"):
            has_pkg = self.messageBuilder._prepare_has_pkg_msg()
            check.is_true(has_pkg, f"❌ 【{msg_type}】消息添加表情失败")


    @allure.story("长按菜单操作专项：撤回")
    @allure.title("长按菜单操作专项：撤回-状态：已完成")
    @pytest.mark.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("msg_type", ["text", "emoji", "image", "package", "voice", "video", "position", "card", "file"])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)
    def test_long_press_action_recall(self, strategy, msg_type):
        
        with allure.step(f"1. 进入聊天页面"):
            self.chatListPage.enter_chat(strategy.name)
            base_msg_text = f"【{msg_type}】长按【撤回】功能专项"
            self.chatPage.send_message(base_msg_text)

        with allure.step(f"2. 校验【{msg_type}】长按菜单项"):
            strategy_model = MessageTypeStrategy.get_strategy(msg_type)
            if "撤回/删除" not in strategy_model.expected_menus:
                pytest.skip(f"⏭️ {msg_type} 消息类型不支持【撤回】，自动跳过")

        with allure.step(f"3. 前置准备：进入聊天页面并发送一条【{msg_type}】消息"):
            self._prepare_message(msg_type)


        with allure.step(f"4. 执行长按并点击【撤回】"):
            self.longPressPage.long_press_last_message()
            is_ok = self.longPressPage._execute_and_verify_menu_item("撤回")
            check.is_true(is_ok, "❌ 长按点击【撤回】失败")

        with allure.step(f"5. 结果验证：验证撤回效果"):
            withmsg, smsg = self.chatPage.get_withdraw_message(index=-1)
            check.is_in("您撤回了一条消息", withmsg, f"❌ 【{msg_type}】消息撤回失败，没有显示撤回标识")
            check.equal(smsg, base_msg_text, f"❌ 【{msg_type}】消息撤回失败，撤回消息与正常消息不匹配")
        

    @allure.story("长按菜单操作专项：删除")
    @allure.title("长按菜单操作专项：删除-状态：已完成")
    @pytest.mark.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("msg_list", [
        ["text", "emoji", "image", "voice", "video", "position", "card", "file", "package"]
    ], ids=["全量消息类型"])
    @pytest.mark.parametrize("strategy", [PRIVATE_USER1, GROUP_STRATEGY], ids=lambda s: s.desc)    
    def test_long_press_action_delete(self, strategy, msg_list):
        allure.dynamic.title(f"【删除专项】 {strategy.desc} - 批量处理")
        
        with allure.step(f"1. 进入聊天页面"):
            self.chatListPage.enter_chat(strategy.name)
            self.chatPage.send_message(f"【{msg_list}】长按【删除】功能专项")
        
        with allure.step(f"2. 校验支持【删除】的菜单项"):
            for m_type in msg_list:
                strategy_model = MessageTypeStrategy.get_strategy(m_type)
                if "撤回/删除" not in strategy_model.expected_menus:
                    pytest.skip(f"⏭️ {m_type} 消息类型不支持【删除】，自动跳过")

        pre_data = {}
        successfully_sent_types = []

        with allure.step(f"3. 集中火力：准备多条不同消息并预存数据"):
            for m_type in msg_list:
                try:
                    self._prepare_message(m_type)
                    
                    pre_data[m_type] = self.messageBuilder.get_message_feature(m_type, expect_missing=False)
                    
                    if m_type == "file":
                        file_status = pre_data[m_type].get("文件状态", "")
                        if file_status:
                            check.is_in("发送成功", file_status, f"❌ 文件消息发送失败")
                    
                    successfully_sent_types.append(m_type)
                except Exception as e:
                    logger.error(f"❌ 发送 {m_type} 消息过程中崩溃: {e}")
                    for _ in range(5):
                        if self.chatPage.is_element_exist(ChatLocator.ADD_BUTTON, timeout=1):
                            logger.info(f"✅ 已成功从 {m_type} 失败状态恢复到聊天页面，继续执行下一类型")
                            break
                        logger.warning(f"⚠️ {m_type} 测试卡在其他页面，正在尝试按返回键恢复...")
                        self.chatPage.back_to_chat_page()

        if not successfully_sent_types:
            pytest.fail("❌ 所有类型的消息发送均失败，无法进行后续验证！")

        with allure.step(f"4. 统一挂机等待：只等一次 2 分钟"):
            if strategy.name == "测试0222" or strategy.is_admin != True:
                self.chatPage.wait_for_x_minutes(120)

        with allure.step(f"5. 批量验证并从下往上删除"):
            for m_type in reversed(successfully_sent_types):
                logger.info(f"正在执行删除验证，类型: {m_type}")
                
                try:
                    self.longPressPage.long_press_last_message()
                    is_ok = self.longPressPage._execute_and_verify_menu_item("删除")
                    self.chatPage.click_del_confirm()
                    check.is_true(is_ok, f"❌ {m_type} 长按点击【删除】失败")
                    
                    current = self.messageBuilder.get_message_feature(m_type, expect_missing=True)
                    check.not_equal(current, pre_data[m_type], f"❌ 【{m_type}】删除后消息仍存在")
                except Exception as e:
                    logger.error(f"❌ 验证删除 {m_type} 时发生异常: {e}")

    
