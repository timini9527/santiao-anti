import time
from appium.webdriver.common.appiumby import AppiumBy
from common.base_page import BasePage
from core.logger_utils import logger
from pages.chat.core.chat_page import ChatPage
from locators.chat_options.voice.chat_voice_locator import ChatVoiceLocator


class ChatVoicePage(ChatPage):
    """
    负责处理聊天页面下的语音相关功能：例如按住说话、试听、取消、听筒外放切换等
    """

    # 点击按住说话按钮
    def click_voice_press_button(self):
        """点击聊天页面底部的按住说话按钮，进入语音录制模式"""
        self.click(ChatVoiceLocator.VOICE_PRESS_BUTTON)
        logger.info("✔️ 点击按住说话按钮，进入语音录制模式")

    # 获取按住说话按钮
    def get_voice_press_button(self):
        """获取按住说话按钮元素，用于后续的位置计算和长按操作"""
        btn = self.find_element(ChatVoiceLocator.VOICE_PRESS_BUTTON, timeout=2)
        if btn:
            logger.info("✔️ 成功获取按住说话按钮")
        else:
            logger.warning("⚠️ 未找到按住说话按钮")
        return btn

    # 点击试听按钮/操作区
    def click_voice_press_button_listen(self):
        """点击试听按钮（录音过程中滑动至此区域后松手进入试听）"""
        self.click(ChatVoiceLocator.VOICE_RECORD_PREVIEW_ACTION)
        logger.info("✔️ 点击试听按钮，准备进入语音试听模式")

    # 获取试听按钮/操作区
    def get_voice_press_button_listen(self):
        """获取试听按钮元素，用于后续位移滑动的目标坐标计算"""
        btn = self.find_element(ChatVoiceLocator.VOICE_RECORD_PREVIEW_ACTION, timeout=2)
        if btn:
            logger.info("✔️ 成功获取试听按钮")
        else:
            logger.warning("⚠️ 未找到试听按钮，可能尚未进入录音状态")
        return btn

    # 点击取消发送按钮/操作区
    def click_voice_press_button_cancel(self):
        """点击取消发送按钮（录音过程中滑动至此区域后松手）"""
        self.click(ChatVoiceLocator.VOICE_RECORD_CANCEL_ACTION)
        logger.info("✔️ 点击取消发送按钮，本次录音已取消")

    # 获取取消发送按钮/操作区
    def get_voice_press_button_cancel(self):
        """获取取消发送按钮元素，用于后续位移滑动的目标坐标计算"""
        btn = self.find_element(ChatVoiceLocator.VOICE_RECORD_CANCEL_ACTION, timeout=2)
        if btn:
            logger.info("✔️ 成功获取取消发送按钮")
        else:
            logger.warning("⚠️ 未找到取消发送按钮，可能尚未进入录音状态")
        return btn

    # 点击试听下取消按钮
    def click_voice_press_button_retry(self):
        """点击试听界面下的取消按钮，放弃发送"""
        self.click(ChatVoiceLocator.VOICE_PREVIEW_CANCEL_ACTION)
        logger.info("✔️ 已点击试听取消按钮，放弃发送")
        time.sleep(0.5)

    # 点击试听下发送按钮
    def click_voice_press_button_send(self):
        """点击试听界面下的发送按钮，发送语音"""
        self.click(ChatVoiceLocator.VOICE_PREVIEW_SEND_ACTION)
        logger.info("✔️ 已点击试听发送按钮，发送语音")
        time.sleep(0.5)

    # 点击听筒或外放切换按钮
    def click_voice_press_button_speaker(self):
        """点击试听界面的听筒/外放切换按钮"""
        self.click(ChatVoiceLocator.VOICE_PREVIEW_ROUTE_ACTION)
        logger.info("✔️ 已点击试听页面的听筒/外放切换按钮")

    # 获取听筒或外放切换按钮
    def get_voice_press_button_speaker_icon(self):
        """获取听筒/外放切换按钮元素"""
        btn = self.find_element(ChatVoiceLocator.VOICE_PREVIEW_ROUTE_ACTION, timeout=2)
        if btn:
            logger.info("✔️ 成功获取听筒/外放切换按钮")
        else:
            logger.warning("⚠️ 未找到听筒/外放切换按钮")
        return btn

    # 获取听筒或外放按钮文字
    def get_voice_press_button_speaker_text(self) -> str:
        """获取听筒/外放切换按钮当前显示的文字（用于判断当前播放模式）"""
        text = self.get_attribute(ChatVoiceLocator.VOICE_PREVIEW_ROUTE_LABEL, 'text', raise_exception=False) or ""
        logger.info(f"✔️ 当前听筒/外放模式文字: 【{text}】")
        return text

    # 获取听筒或外放状态文案
    def get_voice_preview_route_status_text(self) -> str:
        """获取试听界面听筒/外放状态文案"""
        text = self.get_attribute(ChatVoiceLocator.VOICE_PREVIEW_ROUTE_STATUS, 'text', raise_exception=False) or ""
        logger.info(f"✔️ 当前听筒/外放状态文案: 【{text}】")
        return text

    # 点击播放或暂停试听按钮
    def click_voice_press_button_play_or_pause(self):
        """点击试听界面的播放/暂停按钮"""
        self.click(ChatVoiceLocator.VOICE_PREVIEW_PLAY_ACTION)
        time.sleep(0.5)
        logger.info("✔️ 已点击试听页面的播放/暂停按钮")

    # 获取语音实时时长
    def get_voice_press_button_time(self) -> str:
        """获取录音或试听模式下的语音时长文字（如 11'' 或 00:11）"""
        text = self.get_attribute(ChatVoiceLocator.VOICE_RECORD_TIME, 'text', raise_exception=False) or ""
        logger.info(f"✔️ 语音时长显示: 【{text}】")
        return text

    # 获取录音提示文本
    def get_voice_text(self) -> str:
        """获取录音过程中提示框内显示的文字（如 '松开 发送' 等）"""
        text = self.get_attribute(ChatVoiceLocator.VOICE_RECORD_HINT, 'text', raise_exception=False) or ""
        logger.info(f"✔️ 录音提示框文字: 【{text}】")
        return text

    # 获取语音消息不同文案显示
    def get_voice_message_text(self, text: str) -> str:
        """根据传入的标识文字获取对应语音消息气泡中的文案"""
        result = self.get_attribute(ChatVoiceLocator.get_voice_message_locator(text), 'text', raise_exception=False) or ""
        logger.info(f"✔️ 语音气泡消息文字 [{text}]: 【{result}】")
        return result

    # 获取最新语音消息发送状态
    def get_latest_voice_message_status(self, time_val: int):
        """获取最新一条语音消息的发送状态元素（有则代表发送失败，气泡上会显示红点）"""
        locator = ChatVoiceLocator.get_latest_voice_message_status_locator(time_val)
        elem = self.find_element(locator, timeout=2, expect_missing=True)
        if elem:
            logger.warning(f"⚠️ [{time_val}s] 语音消息存在失败状态红点（发送失败）")
        else:
            logger.info(f"✔️ [{time_val}s] 语音消息无失败状态红点，发送正常")
        return elem

    # 发送长按语音 (基础发送流程)
    def send_voice_message(self, hold_time: int = 60) -> dict:
        """
        发送长按语音 (包含长按并分段监听机制，纯 W3C 协议实现)
        :param hold_time: 悬停时长 (秒)
        :return: 返回一个字典，包含可能出现的 toast 提示
        """
        result = {"toast": "", "warning_text": ""}

        voice_button = self.get_voice_press_button()
        if not voice_button:
            raise RuntimeError("未找到按住说话按钮")

        start_x, start_y = self.get_element_center(voice_button)

        if hold_time < 50:
            logger.info(f"👉 短时间录音 ({hold_time}秒)，直接使用 W3C 触屏长按...")
            actions, touch_input = self.init_w3c_actions()
            self.pointer_down_and_hold(actions, start_x, start_y, hold_time)
            self.pointer_up_at_location(touch_input, start_x, start_y)
            if hold_time == 0:
                result["toast"] = self.get_toast()
            return result

        # ========================================================
        # 1. 开启长时间录音
        # ========================================================
        logger.info(f"👉 开启长录音模式 ({hold_time}秒)，启动纯 W3C 长按监听...")
        actions, touch_input = self.init_w3c_actions()
        self.pointer_down_and_hold(actions, start_x, start_y, hold_time)
        self.pointer_up_at_location(touch_input, start_x, start_y)
        logger.info("👉 手指松开，语音录制结束。")
        if hold_time == 0:
            result["toast"] = self.get_toast()
        return result

    # 语音消息取消发送
    def verify_voice_message_cancel(self, press_time: int = 1, hold_time: int = 5) -> bool:
        """
        按住录音 -> 动态定位取消按钮 -> 滑动过去 -> 悬停 -> 松手取消
        """
        actions, touch_input = self.init_w3c_actions()

        voice_btn = self.get_voice_press_button()
        if not voice_btn:
            raise RuntimeError("未找到按住说话按钮")

        start_x, start_y = self.get_element_center(voice_btn)
        logger.info(f"👉 第一阶段：按住录音按钮 ({start_x}, {start_y})")
        self.pointer_down_and_hold(actions, start_x, start_y, press_time)

        logger.info("👀 录音中... 动态寻找取消按钮坐标...")
        cancel_btn = self.get_voice_press_button_cancel()
        if not cancel_btn:
            self.pointer_up_at_location(touch_input, start_x, start_y)
            raise RuntimeError("❌ 录音中未弹出取消按钮！")

        target_x, target_y = self.get_element_center(cancel_btn)
        logger.info(f"🎯 成功锁定取消按钮，坐标: ({target_x}, {target_y})")

        actions.w3c_actions.clear_actions()
        actions.w3c_actions.pointer_action.move_to_location(start_x, start_y)
        touch_input.create_pointer_move(x=target_x, y=target_y, duration=500, origin="viewport")

        logger.info(f"👉 滑动到取消按钮，并悬停 {hold_time} 秒...")
        actions.w3c_actions.pointer_action.pause(hold_time)
        actions.perform()

        logger.info("👉 松开手指，取消发送...")
        self.pointer_up_at_location(touch_input, target_x, target_y)
        time.sleep(0.5)
        return True

    # 语音消息滑动试听
    def slide_to_listen_mode(self, press_time: int = 1, hold_time: int = 5) -> bool:
        """
        按住录音 -> 动态定位试听按钮 -> 滑动过去 -> 悬停 -> 松手进入试听
        """
        actions, touch_input = self.init_w3c_actions()

        voice_btn = self.get_voice_press_button()
        if not voice_btn:
            raise RuntimeError("未找到按住说话按钮")

        start_x, start_y = self.get_element_center(voice_btn)
        logger.info(f"👉 第一阶段：按住录音按钮 ({start_x}, {start_y})")
        self.pointer_down_and_hold(actions, start_x, start_y, press_time)

        logger.info("👀 录音中... 动态寻找试听按钮坐标...")
        preview_btn = self.get_voice_press_button_listen()
        if not preview_btn:
            self.pointer_up_at_location(touch_input, start_x, start_y)
            raise RuntimeError("❌ 录音中未弹出试听按钮！")

        target_x, target_y = self.get_element_center(preview_btn)
        logger.info(f"🎯 成功锁定试听按钮，坐标: ({target_x}, {target_y})")

        actions.w3c_actions.clear_actions()
        actions.w3c_actions.pointer_action.move_to_location(start_x, start_y)
        touch_input.create_pointer_move(x=target_x, y=target_y, duration=500, origin="viewport")

        logger.info(f"👉 滑动到试听按钮，并悬停 {hold_time} 秒...")
        actions.w3c_actions.pointer_action.pause(hold_time)
        actions.perform()

        logger.info("👉 松开手指，准备进入试听模式...")
        self.pointer_up_at_location(touch_input, target_x, target_y)
        time.sleep(0.5)
        return True

    # 获取语音消息列表快照
    def get_voice_list_snapshot(self, role: str = 'sender') -> dict:
        """ 在执行 发送/取消 动作之前调用，拍摄当前语音消息列表的基准快照 """
        try:
            side = 'sent' if role == 'sender' else 'received'
            elems = self.get_message_elements('videoDuration', side=side, expect_missing=True)
            if not elems:
                logger.info(f"📷 [{role}] 语音消息列表快照：当前无消息（count=0）")
                return {"count": 0, "last_elem_id": None}

            snapshot = {
                "count": len(elems),
                "last_elem_id": elems[-1].id
            }
            logger.info(f"📷 [{role}] 语音消息列表快照：count={snapshot['count']}, last_id={snapshot['last_elem_id']}")
            return snapshot
        except Exception as e:
            logger.error(f"❌ 获取语音消息快照时异常: {e}")
            return {"count": 0, "last_elem_id": None}

    # 验证语音消息显示
    def verify_voice_message_display(self, expected_time: int, pre_snapshot: dict, expect_sent: bool = True, role: str = 'sender') -> bool:
        """
        验证发出的最新语音消息
        :param expected_time: 预期的语音时长 (秒)
        :param pre_snapshot: 执行操作前获取的快照字典
        :param expect_sent: True 表示预期发送成功，False 表示预期取消发送(未发送)
        """
        try:
            side = 'sent' if role == 'sender' else 'received'
            elems = self.get_message_elements('videoDuration', side=side, expect_missing=True)
            if not elems:
                if expect_sent:
                    logger.error("❌ 验证失败：消息列表为空，未找到任何语音消息气泡")
                else:
                    logger.info("✅ 验证通过：预期取消发送，消息列表为空符合预期")
                return False if expect_sent else True

            current_count = len(elems)
            current_last_elem = elems[-1]
            logger.info(f"📊 快照对比 - 前: {pre_snapshot}, 当前: count={current_count}, last_id={current_last_elem.id}")

            voice_message = current_last_elem.get_attribute('text') or "0"
            actual_time = int(voice_message.replace('"', '').replace("'", ""))
            logger.info(f"⏱️ 语音时长对比: 实际={actual_time}s, 预期={expected_time}s")

            is_dom_changed = (current_count > pre_snapshot["count"]) or (current_last_elem.id != pre_snapshot["last_elem_id"])

            if expect_sent:
                if not is_dom_changed:
                    logger.error("❌ 验证失败：DOM 没有任何变化，未生成新气泡！")
                    return False

                status_elem = self.get_latest_voice_message_status(actual_time)
                if status_elem:
                    logger.error("❌ 验证失败：虽然生成了气泡，但带有红色发送失败感叹号！")
                    return False

                is_time_match = abs(actual_time - expected_time) <= 2
                if is_time_match:
                    logger.info(f"✅ 验证通过：语音消息发送成功，{actual_time}s ≈ {expected_time}s（误差在 ±2s 内）")
                else:
                    logger.error(f"❌ 验证失败：语音时长不匹配，实际 {actual_time}s，预期 {expected_time}s，超出 ±2s 容差")
                return is_time_match
            else:
                if is_dom_changed:
                    logger.error("❌ 验证失败：预期取消发送，但聊天界面却刷出了新消息！")
                    return False
                logger.info("✅ 验证通过：预期取消发送，语音消息列表未发生变化")
                return True
        except Exception as e:
            logger.error(f"验证语音气泡时发生异常: {e}")
            return False

    # 验证是否进入试听模式
    def is_in_preview_mode(self) -> bool:
        """
        验证是否成功进入了试听模式 (特征：屏幕上出现试听界面的播放按钮或发送按钮)
        """
        try:
            play_btn = self.find_element(ChatVoiceLocator.VOICE_PREVIEW_PLAY_ACTION, timeout=3)
            if play_btn is not None:
                logger.info("✅ 当前已进入试听模式（播放/暂停按钮可见）")
                return True
            else:
                logger.warning("⚠️ 未检测到播放/暂停按钮，可能尚未进入试听模式")
                return False
        except Exception:
            logger.warning("⚠️ 试听模式检测异常，判定未进入试听模式")
            return False

    # 获取试听模式下的时间
    def get_preview_mode_time(self) -> int:
        """获取试听模式下的语音时长（秒）"""
        listen_time = self.get_voice_press_button_time()
        if ":" in listen_time:
            minute, second = listen_time.split(":")
            total_seconds = int(minute) * 60 + int(second)
        else:
            cleaned = listen_time.replace('"', '').replace("'", "").strip()
            total_seconds = int(cleaned) if cleaned.isdigit() else 0
        logger.info(f"✔️ 试听模式语音总时长: {listen_time} → {total_seconds} 秒")
        return total_seconds

    # 验证播放模式和播放状态
    def is_in_playing_mode(self, play_mode: str, play_status: str = "") -> bool:
        """验证当前语音是否处于指定的播放模式"""
        logger.info(f"🔍 校验播放模式: play_mode={play_mode}, play_status={play_status}")
        play_btn = self.find_element(ChatVoiceLocator.VOICE_PREVIEW_PLAY_ACTION, timeout=2)

        if play_mode in ("play", "pause"):
            return play_btn is not None
        elif play_mode in ("earpiece", "speaker"):
            current_route_text = self.get_voice_press_button_speaker_text()
            if play_mode not in current_route_text.lower():
                logger.info(f"🔄 点击切换听筒/外放模式...")
                self.click_voice_press_button_speaker()
            return True
        return False
