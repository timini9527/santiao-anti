import time
from typing import Optional
from common.base_page import BasePage
from locators.chat.call.call_locator import CallLocator
from core.logger_utils import logger


class CallPage(BasePage):
    """音视频通话页面 (AVChat / Call Activity) Page Object"""

    # 音视频 - 等待进入通话页面
    def wait_call_page_load(self, timeout: int = 10) -> bool:
        """
        音视频 - 等待进入通话页面
        :param timeout: 等待超时时间（秒）
        :return: 页面是否加载成功
        """
        st = self.is_element_exist(CallLocator.IV_HANGUP, timeout=timeout, raise_exception=False)
        if st:
            logger.info("📞 [Action-Call] 等待进入通话页面成功")
        else:
            logger.warning("📞 [Action-Call] 等待进入通话页面失败")
        return st

    # 音视频 - 等待通话页面关闭退出
    def wait_call_page_close(self, timeout: int = 60) -> bool:
        """
        音视频 - 等待通话页面关闭退出
        :param timeout: 等待超时时间（秒）
        :return: 页面是否成功关闭退出
        """
        logger.info(f"⏳ [Action-Call] 等待通话页面关闭退出 (超时: {timeout}s)")
        return self.wait_until_element_disappear(CallLocator.IV_HANGUP, timeout=timeout)

    # 音视频 - 等待进入被叫来电页面
    def wait_incoming_call_page_load(self, timeout: int = 10) -> bool:
        """
        音视频 - 等待进入被叫来电振铃页面
        :param timeout: 等待超时时间（秒）
        :return: 来电振铃页面是否加载成功
        """
        st = self.is_element_exist(CallLocator.IV_RECEIVE, timeout=timeout, raise_exception=False)
        if st:
            logger.info("📞 [Action-Call] 等待进入被叫来电页面成功")
        else:
            logger.warning("📞 [Action-Call] 等待进入被叫来电页面失败")
        return st

    # 音视频 - 主动挂断或取消当前呼叫/通话
    def hangup(self) -> None:
        """
        音视频 - 主动挂断或取消当前通话
        """
        logger.info("📞 [Action-Call] 尝试主动挂断/取消通话")
        self.click(CallLocator.IV_HANGUP)
        time.sleep(1)

    # 音视频 - 被叫接听通话
    def accept(self) -> None:
        """
        音视频 - 被叫接听当前通话
        """
        logger.info("📞 [Action-Call] 点击【接听】通话")
        self.click(CallLocator.IV_RECEIVE)
        time.sleep(1)

    # 音视频 - 被叫拒绝通话
    def reject(self) -> None:
        """
        音视频 - 被叫拒绝当前通话
        """
        logger.info("📞 [Action-Call] 点击【拒绝】通话")
        self.click(CallLocator.IV_REFUSE)
        time.sleep(1)

    # 音视频 - 获取被叫来电通知文本
    def get_incoming_notify_text(self) -> Optional[str]:
        """
        音视频 - 获取被叫来电提示文本（如“邀请你语音通话”/“邀请你视频通话”）
        :return: 来电提示文本内容，获取失败时返回 None
        """
        logger.info("📞 [Action-Call] 获取被叫来电提示文本")
        text = self.get_attribute(CallLocator.TV_AVCHAT_NOTIFY, "text", raise_exception=False)
        logger.info(f"📞 [Action-Call] 获取来电提示文本结果: {text}")
        return text

    # 音视频 - 点击最小化悬浮窗
    def minimize_window(self) -> None:
        """
        音视频 - 点击最小化悬浮窗
        """
        logger.info("📞 [Action-Call] 点击最小化通话悬浮窗")
        self.click(CallLocator.AVCHAT_MINI)

    # 音视频 - 切换麦克风静音状态
    def switch_microphone(self) -> None:
        """
        音视频 - 切换麦克风开关状态
        """
        logger.info("📞 [Action-Call] 点击切换麦克风")
        self.click(CallLocator.IV_MICROPHONE_SWITCH)

    # 音视频 - 切换扬声器/免提状态
    def switch_speaker(self) -> None:
        """
        音视频 - 切换扬声器/免提开关状态
        """
        logger.info("📞 [Action-Call] 点击切换扬声器")
        self.click(CallLocator.IV_SPEAKER_SWITCH)

    # 音视频 - 切换/翻转摄像头
    def switch_camera(self) -> None:
        """
        音视频 - 翻转摄像头
        """
        logger.info("📞 [Action-Call] 点击翻转摄像头")
        self.click(CallLocator.IV_VIDEO_CAMERA_SWITCH)

    # 音视频 - 获取当前通话时长
    def get_call_duration(self) -> Optional[str]:
        """
        音视频 - 获取当前通话计时时长
        :return: 通话时长文本（例如 "00:15"），获取失败时返回 None
        """
        logger.info("📞 [Action-Call] 获取当前通话计时时长")
        duration = self.get_attribute(CallLocator.AVCHAT_VIDEO_TIME, "text", raise_exception=False)
        logger.info(f"📞 [Action-Call] 获取通话时长结果: {duration}")
        return duration
