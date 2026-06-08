import time
from selenium.webdriver import ActionChains
from appium.webdriver.common.appiumby import AppiumBy
from common.base_page import BasePage
from core.logger_utils import logger
from pages.chat.chat_page import ChatPage
from locators.chat_options.voice.chat_voice_locator import ChatVoiceLocator



class ChatVoicePage(ChatPage):
    """
    负责处理聊天页面下的语音相关功能：例如按住说话、试听、重发、取消、听筒外放等
    """
    
    # 

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

    # 点击试听按钮
    def click_voice_press_button_listen(self):
        """点击试听按钮（录音过程中滑动至此区域后松手进入试听）"""
        self.click(ChatVoiceLocator.VOICE_PRESS_BUTTON_LISTEN)
        logger.info("✔️ 点击试听按钮，准备进入语音试听模式")

    # 获取试听按钮
    def get_voice_press_button_listen(self):
        """获取试听按钮元素，用于后续位移滑动的目标坐标计算"""
        btn = self.find_element(ChatVoiceLocator.VOICE_PRESS_BUTTON_LISTEN, timeout=2)
        if btn:
            logger.info("✔️ 成功获取试听按钮")
        else:
            logger.warning("⚠️ 未找到试听按钮，可能尚未进入录音状态")
        return btn

    # 点击取消发送按钮
    def click_voice_press_button_cancel(self):
        """点击取消发送按钮（录音过程中滑动至此区域后松手）"""
        self.click(ChatVoiceLocator.VOICE_PRESS_BUTTON_CANCEL)
        logger.info("✔️ 点击取消发送按钮，本次录音已取消")

    # 获取取消发送按钮
    def get_voice_press_button_cancel(self):
        """获取取消发送按钮元素，用于后续位移滑动的目标坐标计算"""
        btn = self.find_element(ChatVoiceLocator.VOICE_PRESS_BUTTON_CANCEL, timeout=2)
        if btn:
            logger.info("✔️ 成功获取取消发送按钮")
        else:
            logger.warning("⚠️ 未找到取消发送按钮，可能尚未进入录音状态")
        return btn

    # 点击试听下取消按钮
    def click_voice_press_button_retry(self):
        self.click(ChatVoiceLocator.VOICE_PRESS_BUTTON_RETRY)
        logger.info("已点击试听取消按钮，放弃发送")
        time.sleep(0.5)

    # 点击试听下发送按钮
    def click_voice_press_button_send(self):
        self.click(ChatVoiceLocator.VOICE_PRESS_BUTTON_SEND)
        logger.info("已点击试听发送按钮，发送语音")
        time.sleep(0.5)

    # 点击听筒或外放按钮整个容器
    def click_voice_press_button_speaker(self):
        self.click(ChatVoiceLocator.VOICE_PRESS_BUTTON_SPEAKER)
        logger.info("已点击试听页面的听筒/外放切换按钮容器")
    
    # 点击听筒或外放按钮
    def click_voice_press_button_speaker_icon(self):
        self.click(ChatVoiceLocator.VOICE_PRESS_BUTTON_SPEAKER_IN_LISTEN)
        logger.info("已点击试听页面的听筒/外放切换按钮")
    
    # 获取听筒或外放按钮
    def get_voice_press_button_speaker_icon(self):
        """获取听筒/外放切换按钮元素"""
        btn = self.find_element(ChatVoiceLocator.VOICE_PRESS_BUTTON_SPEAKER_IN_LISTEN, timeout=2)
        if btn:
            logger.info("✔️ 成功获取听筒/外放切换按钮")
        else:
            logger.warning("⚠️ 未找到听筒/外放切换按钮")
        return btn

    # 获取听筒或外放按钮文字
    def get_voice_press_button_speaker_text(self):
        """获取听筒/外放切换按钮当前显示的文字（用于判断当前播放模式）"""
        text = self.get_attribute(ChatVoiceLocator.VOICE_PRESS_BUTTON_SPEAKER_IN_LISTEN_TEXT, 'text')
        logger.info(f"✔️ 当前听筒/外放模式文字: 【{text}】")
        return text

    # 点击播放或暂停试听按钮
    def click_voice_press_button_play_or_pause(self):
        self.click(ChatVoiceLocator.VOICE_PRESS_BUTTON_PLAY_OR_PAUSE)
        time.sleep(0.5)
        logger.info("已点击试听页面的播放/暂停按钮")

    # 获取播放波形效果
    def get_voice_press_button_wave(self):
        """获取试听模式下的语音波形动画元素（用于判断是否有声音播出）"""
        elem = self.find_element(ChatVoiceLocator.VOICE_PRESS_BUTTON_WAVE)
        logger.info(f"✔️ 获取波形元素: {'已找到' if elem else '未找到'}")
        return elem

    # 获取语音时长
    def get_voice_press_button_time(self) -> str:
        """获取试听模式下的语音计时器文字（格式为 mm:ss）"""
        text = self.get_attribute(ChatVoiceLocator.VOICE_PRESS_BUTTON_TIME, 'text')
        logger.info(f"✔️ 试听模式语音时长显示: 【{text}】")
        return text

    # 暂停时，获取准备试听语音内容
    def get_voice_prepare_listen(self) -> str:
        """获取暂停状态下准备试听的提示文字"""
        text = self.get_attribute(ChatVoiceLocator.VOICE_PREPARE_LISTEN, 'text')
        logger.info(f"✔️ 暂停状态试听提示文字: 【{text}】")
        return text

    # 播放时，获取听筒播放倒计时
    def get_voice_play_soon_earpiece(self) -> str:
        """获取听筒播放模式下的剩余倒计时文字"""
        text = self.get_attribute(ChatVoiceLocator.VOICE_PLAY_SOON_EARPIECE, 'text')
        logger.info(f"✔️ 听筒播放倒计时: 【{text}】")
        return text


    
    # 播放时，获取扬声器播放倒计时
    def get_voice_play_soon_speaker(self) -> str:
        """获取扬声器播放模式下的剩余倒计时文字"""
        text = self.get_attribute(ChatVoiceLocator.VOICE_PLAY_SOON_SPEAKER, 'text')
        logger.info(f"✔️ 扬声器播放倒计时: 【{text}】")
        return text

    # 获取文本内容
    def get_voice_text(self) -> str:
        """获取录音过程中提示框内显示的文字（如 '松开发送'、'松开取消' 等）"""
        text = self.get_attribute(ChatVoiceLocator.VOICE_HINT_BOX, 'text')
        logger.info(f"✔️ 录音提示框文字: 【{text}】")
        return text

    # 获取语音消息不同文案显示
    def get_voice_message_text(self, text: str) -> str:
        """根据传入的标识文字获取对应语音消息气泡中的文案"""
        result = self.get_attribute(ChatVoiceLocator.get_voice_message_locator(text), 'text')
        logger.info(f"✔️ 语音气泡消息文字 [{text}]: 【{result}】")
        return result

    # 获取最新语音消息发送状态
    def get_latest_voice_message_status(self, time: int):
        """获取最新一条语音消息的发送状态元素（有则代表发送失败，气泡上会显示红点）"""
        locator = ChatVoiceLocator.get_latest_voice_message_status_locator(time)
        elem = self.find_element(locator, timeout=2)
        if elem:
            logger.warning(f"⚠️ [{time}s] 语音消息存在失败状态红点（发送失败）")
        else:
            logger.info(f"✔️ [{time}s] 语音消息无失败状态红点，发送正常")
        return elem
    
    # 发送长按语音 (基础发送流程)
    def send_voice_message(self, hold_time: int = 60) -> dict:
        """
        发送长按语音 (包含长按并分段监听机制，纯 W3C 协议实现)
        :param hold_time: 悬停时长 (秒)
        :return: 返回一个字典，包含可能出现的 toast 和倒计时警告文本
        """
        result = {"toast": "", "warning_text": ""}

        voice_button = self.get_voice_press_button()
        if not voice_button:
            raise RuntimeError("未找到按住说话按钮")
            
        start_x, start_y = self.get_element_center(voice_button)

        if hold_time < 50:
            logger.info(f"👉 短时间录音 ({hold_time}秒)，直接使用长按...")
            self.long_press_action(voice_button, hold_time=hold_time * 1000)
            if hold_time == 0:
                result["toast"] = self.toast_message()
            return result

        # ========================================================
        # 1. 初始化动作输入源
        # ========================================================
        actions, touch_input = self.init_w3c_actions()

        # ========================================================
        # 2. 阶段一：长按语音按钮前 48 秒
        # ========================================================
        logger.info(f"👉 开启长录音模式 ({hold_time}秒)，启动纯 W3C 长按监听...")
        
        self.pointer_down_and_hold(actions, start_x, start_y, 48) # 首次发送指令（阻塞约48秒，此期间手指一直按着）

        # ========================================================
        # 3. 阶段二：开启高频短时按压 + 抓取倒计时警告
        # ========================================================
        logger.info("👀 48秒已过，倒计时即将出现，开始动态轮询...")
        start_time = time.time()
        
        # 多轮询2秒作为系统容错空间
        while time.time() - start_time < (hold_time - 48 + 2): 
            try:
                # 尝试抓取警告文案，设置极短的超时以防止线程长期阻塞 (0.5秒)
                warning_elem = self.find_element(ChatVoiceLocator.VOICE_HINT_TIME_LIMIT, timeout=2)
                if warning_elem:
                    result["warning_text"] = warning_elem.text
                    logger.info(f"✅ 成功捕获到倒计时警告: {result['warning_text']}")
                    break
            except Exception:
                pass
                
            # 发送心跳延续指令，告之系统手指还在按压，持续0.5秒
            actions.w3c_actions.clear_actions()
            actions.w3c_actions.pointer_action.move_to_location(start_x, start_y)
            actions.w3c_actions.pointer_action.pause(0.5)
            actions.perform()

        # ========================================================
        # 4. 阶段三：补齐剩余的长按时间（如果有）
        # ========================================================
        elapsed = time.time() - start_time
        remaining = max(0, (hold_time - 48) - elapsed)
        if remaining > 0.1:
            logger.info(f"⏳ 继续按压剩余的 {remaining:.1f} 秒...")
            actions.w3c_actions.clear_actions()
            actions.w3c_actions.pointer_action.move_to_location(start_x, start_y)
            actions.w3c_actions.pointer_action.pause(remaining)
            actions.perform()

        # ========================================================
        # 5. 阶段四：抬起松开手指，结束录音
        # ========================================================
        logger.info("👉 手指松开，语音录制结束。")
        self.pointer_up_at_location(touch_input, start_x, start_y)

        return result
    
    # 语音消息取消发送
    def verify_voice_message_cancel(self, press_time: int = 1, hold_time: int = 10) -> bool:
        """
        按住录音(4s) -> 动态定位取消按钮 -> 滑动过去 -> 悬停(10s) -> 抓取提示 -> 松手
        """
        # 1. 初始化动作输入源 (必须在整个过程中复用同一个 finger 对象，保持按下状态)
        actions, touch_input = self.init_w3c_actions()

        voice_btn = self.get_voice_press_button()
        if not voice_btn:
            raise RuntimeError("未找到按住说话按钮")
        
        start_x, start_y = self.get_element_center(voice_btn)
        logger.info(f"👉 第一阶段：按住录音按钮 ({start_x}, {start_y})")
        self.pointer_down_and_hold(actions, start_x, start_y, press_time) # 第一次发送指令（手指保持按下）

        logger.info("👀 录音中... 动态寻找取消按钮坐标...")
        cancel_btn = self.get_voice_press_button_cancel()
        if not cancel_btn:
            self.pointer_up_at_location(touch_input, start_x, start_y)
            raise RuntimeError("❌ 录音 1 秒后，未弹出取消按钮！")
        
        target_x, target_y = self.get_element_center(cancel_btn)
        logger.info(f"🎯 成功锁定取消按钮，坐标: ({target_x}, {target_y})")

        # 清理之前已执行过的 Actions 队列，准备构造后续的滑动动作 (确保手指状态延续但不重复历史动作)
        actions.w3c_actions.clear_actions()
        actions.w3c_actions.pointer_action.move_to_location(start_x, start_y)
        touch_input.create_pointer_move(x=target_x, y=target_y, duration=500, origin="viewport")

        logger.info(f"👉 滑动到试听按钮，并悬停 {hold_time} 秒...")
        actions.w3c_actions.pointer_action.pause(hold_time)
        actions.perform()

        logger.info("👀 检查是否出现『松开 取消发送』提示文案...")
        is_hover_text_found = False
        try:
            hover_tips = self.find_element(ChatVoiceLocator.VOICE_HINT_CANCEL, timeout=2)
            logger.info(f"✅ 成功捕获到悬停提示: 【{hover_tips.text}】")
            is_hover_text_found = True
        except Exception:
            logger.warning("❌ 未捕获到『松开 取消发送』的提示文案！")

        logger.info("👉 松开手指，取消发送...")
        self.pointer_up_at_location(touch_input, target_x, target_y)
        time.sleep(0.5)

        if not is_hover_text_found:
            return False
        return True 

    # 语音消息试听
    def slide_to_listen_mode(self, press_time: int = 1,hold_time=10) -> bool:
        """
        按住录音(1s) -> 动态定位试听按钮 -> 滑动过去 -> 悬停(10s) -> 抓取提示 -> 松手
        """
        # ========================================================
        # 1. 初始化动作输入源 (必须在整个过程中复用同一个 finger 对象，保持按下状态)
        # ========================================================
        actions, touch_input = self.init_w3c_actions()
        
        # ========================================================
        # 1. 阶段一：【按下录音键并等待 1 秒】
        # ========================================================
        voice_btn = self.get_voice_press_button()
        if not voice_btn:
            raise RuntimeError("未找到按住说话按钮")
            
        start_x, start_y = self.get_element_center(voice_btn)

        logger.info(f"👉 第一阶段：按住录音按钮 ({start_x}, {start_y})")
        
        self.pointer_down_and_hold(actions, start_x, start_y, press_time) # 第一次发送指令（手指保持按下）

        # ========================================================
        # 2. 动态寻找试听按钮坐标
        # ========================================================
        logger.info("👀 录音中... 动态寻找试听按钮坐标...")
        preview_btn = self.get_voice_press_button_listen()
        if not preview_btn:
            self.pointer_up_at_location(touch_input, start_x, start_y)
            raise RuntimeError("❌ 录音 1 秒后，未弹出试听按钮！")
            
        target_x, target_y = self.get_element_center(preview_btn)
        logger.info(f"🎯 成功锁定试听按钮，坐标: ({target_x}, {target_y})")

        # ========================================================
        # 3. 阶段二：【滑动到试听按钮 -> 悬停 10 秒】
        # ========================================================
        # 清理之前已执行过的 Actions 队列，准备构造后续的滑动动作 (确保手指状态延续但不重复历史动作)
        actions.w3c_actions.clear_actions()
        
        # 手指当前还在 start_x, start_y
        actions.w3c_actions.pointer_action.move_to_location(start_x, start_y)
        
        # 从原点缓慢滑动到目标位置
        touch_input.create_pointer_move(x=target_x, y=target_y, duration=500, origin="viewport")
        
        # 悬停 hold_time 秒
        logger.info(f"👉 滑动到试听按钮，并悬停 {hold_time} 秒...")
        actions.w3c_actions.pointer_action.pause(hold_time)
        actions.perform() # 第二次发送指令（手指依然保持按下）

        # ========================================================
        # 4. 在悬停结束前，抓取“松开 试听”的文字
        # ========================================================
        logger.info("👀 检查是否出现『松开 试听』提示文案...")
        is_hover_text_found = False
        try:
            hover_tips = self.find_element(ChatVoiceLocator.VOICE_HINT_AUDITION, timeout=2)
            logger.info(f"✅ 成功捕获到悬停提示: 【{hover_tips.text}】")
            is_hover_text_found = True
        except Exception:
            logger.warning("❌ 未捕获到『松开 试听』的提示文案！")

        # ========================================================
        # 5. 阶段三：【松开手指】
        # ========================================================
        logger.info("👉 松开手指，准备进入试听模式...")
        self.pointer_up_at_location(touch_input, target_x, target_y)
        time.sleep(0.5)
        if not is_hover_text_found:
            return False
        return True

    # 获取语音消息列表快照
    def get_voice_list_snapshot(self, role: str = 'sender') -> dict:
        """
        [核心利器]：在执行 发送/取消 动作之前调用，拍摄当前语音消息列表的基准快照。
        验证时与新快照对比，防止误判旧消息时长恰好相同导致的假阳性。
        """
        try:
            locator = ChatVoiceLocator.get_sent_voice_message_time_locator(role)
            elems = self.find_elements(locator, timeout=2)
            if not elems:
                logger.info(f"📷 [{role}] 语音消息列表快照：当前无消息（count=0）")
                return {"count": 0, "last_elem_id": None}

            snapshot = {
                "count": len(elems),
                "last_elem_id": elems[-1].id  # 底层分配的唯一元素 ID
            }
            logger.info(f"📷 [{role}] 语音消息列表快照：count={snapshot['count']}, last_id={snapshot['last_elem_id']}")
            return snapshot
        except Exception as e:
            logger.error(f"❌ 获取语音消息快照时异常: {e}")
            return {"count": 0, "last_elem_id": None}

     # 验证语音消息显示
    def verify_voice_message_display(self, expected_time: int, pre_snapshot: dict, expect_sent: bool = True, role: str = 'sender') -> bool:
        """
        验证发出的最新语音消息，彻底杜绝相同数据的假阳性误判。
        :param expected_time: 预期的语音时长 (秒)
        :param pre_snapshot: 执行操作前获取的快照字典
        :param expect_sent: True 表示预期发送成功，False 表示预期取消发送(未发送)
        """
        if expected_time > 60:
            self.click_voice_press_button()  # 模拟器需要的操作
            
        try:
            locator = ChatVoiceLocator.get_sent_voice_message_time_locator(role)
            elems = self.find_elements(locator, timeout=2)
            time.sleep(1)
            if not elems:
                if expect_sent:
                    logger.error("❌ 验证失败：消息列表为空，未找到任何语音消息气泡")
                else:
                    logger.info("✅ 验证通过：预期取消发送，消息列表为空符合预期")
                return False if expect_sent else True

            current_count = len(elems)
            current_last_elem = elems[-1]
            logger.info(f"📊 快照对比 - 前: {pre_snapshot}, 当前: count={current_count}, last_id={current_last_elem.id}")
            
            # 获取当前最后一条的时长
            voice_message = current_last_elem.get_attribute('text')
            actual_time = int(voice_message.replace('"', '').replace("'", ""))
            logger.info(f"⏱️ 语音时长对比: 实际={actual_time}s, 预期={expected_time}s")
            
            # 判断 DOM 是否发生了物理新增或滚动
            is_dom_changed = (current_count > pre_snapshot["count"]) or (current_last_elem.id != pre_snapshot["last_elem_id"])

            if expect_sent:
                if not is_dom_changed:
                    logger.error("❌ 验证失败：DOM 没有任何变化，未生成新气泡，说明这是上一条旧消息的时间巧合！")
                    return False

                status_elem = self.get_latest_voice_message_status(actual_time)
                if status_elem is not None:
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
        验证是否成功进入了试听模式 (特征：屏幕上会出现 发送、取消、播放 等试听界面的特有按钮)
        """
        try:
            play_btn = self.find_element(ChatVoiceLocator.VOICE_PRESS_BUTTON_PLAY_OR_PAUSE, timeout=3)
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
        """获取试听模式下的语音时长（秒），将 'mm:ss' 格式转换为整数秒"""
        listen_time = self.get_voice_press_button_time()  # 格式：00:12 / 01:00
        minute, second = listen_time.split(":")
        total_seconds = int(minute) * 60 + int(second)
        logger.info(f"✔️ 试听模式语音总时长: {listen_time} → {total_seconds} 秒")
        return total_seconds

    # 验证是否进入播放模式和播放状态
    def is_in_playing_mode(self, play_mode, play_status) -> bool:
        """验证当前语音是否处于指定的播放模式和播放状态"""
        logger.info(f"🔍 校验播放模式: play_mode={play_mode}, 预期状态文字=【{play_status}】")
        voice_text = self.get_voice_message_text(play_status)
        icon_type_text = self.get_voice_press_button_speaker_text()

        if play_mode == "play":
            result = play_status in voice_text
            logger.info(f"{'✅' if result else '❌'} 播放模式校验: 预期包含 [{play_status}]，实际 [{voice_text}]")
            return result
        elif play_mode == "pause":
            result = play_status == voice_text
            logger.info(f"{'✅' if result else '❌'} 暂停模式校验: 预期精确匹配 [{play_status}]，实际 [{voice_text}]")
            return result
        elif play_mode in ("earpiece", "speaker"):
            if icon_type_text not in play_mode:
                logger.info(f"🔄 当前图标为 [{icon_type_text}]，与目标模式 [{play_mode}] 不匹配，点击切换")
                self.click_voice_press_button_speaker()
            else:
                logger.info(f"✔️ 当前图标 [{icon_type_text}] 已在目标模式 [{play_mode}] 下，无需切换")
            time.sleep(2)
            voice_text = self.get_voice_message_text(play_status)
            result = voice_text in play_status
            logger.info(f"{'✅' if result else '❌'} {play_mode} 模式校验: 预期 [{play_status}] 中包含 [{voice_text}]")
            return result
        else:
            logger.error(f"❌ 不支持的 play_mode 类型: {play_mode}，可选值为 play/pause/earpiece/speaker")
            return False
            
        
    # 待完善
    # 验证语音消息发送失败（出现红点）
    def verify_voice_message_failed(self, expected_time: int, pre_snapshot: dict, role: str = 'sender') -> bool:
        """
        断言极其恶劣的场景（断网、服务器拒绝等）：界面理应吐出气泡，但气泡上钉着一个红色的失败感叹号！
        """
        try:
            locator = ChatVoiceLocator.get_sent_voice_message_time_locator(role)
            elems = self.find_elements(locator, timeout=3) # 网络超时可能需要稍等UI
            if not elems:
                logger.error("❌ 验证失败：断网下理应吐出一个带红点的新气泡，但界面一根毛也没有！")
                return False

            current_count = len(elems)
            current_last_elem = elems[-1]
            
            # 校验是否真冒出了新气泡
            is_dom_changed = (current_count > pre_snapshot["count"]) or (current_last_elem.id != pre_snapshot["last_elem_id"])
            if not is_dom_changed:
                logger.error("❌ 验证失败：没有新的气泡冒出，说明刚才按住说话完全无效！")
                return False

            voice_message = current_last_elem.get_attribute('text')
            actual_time = int(voice_message.replace('"', '').replace("'", ""))
            
            # 定位这个气泡必须附带一个可点击的红色重发按钮
            status_elem = self.get_latest_voice_message_status(actual_time)
            if status_elem is None:
                logger.error("❌ 验证失败：竟然没有红色的失败感叹号？断网下难道消息凭空发出去了吗！")
                return False
                
            return abs(actual_time - expected_time) <= 2
        except Exception as e:
            logger.error(f"验证发送失败态红点时异常: {e}")
            return False



