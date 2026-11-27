from enum import StrEnum


class ToastMsg(StrEnum):
    """
    全局高频业务 Toast 与轻量反馈提示文本枚举
    继承自 StrEnum，具备字符串原生特性（无需调用 .value 即可当 str 使用），提供统一的 IDE 智能补全与常量维护。
    """

    # --------------------------------------------------------------------------
    # 1. 登录与账号状态
    # --------------------------------------------------------------------------
    LOGOUT_SUCCESS = "已退出登录"
    LOGGING_IN = "登录中..."
    VERIFY_CODE_SENT = "验证码已发送"
    RATE_LIMIT_DAILY = "触发天极流控"
    RATE_LIMIT_HOURLY = "触发小时级流控"
    SWITCH_NETWORK = "尝试更换网络环境"

    # --------------------------------------------------------------------------
    # 2. 通用增删改查与媒体操作
    # --------------------------------------------------------------------------
    SAVE_SUCCESS = "保存成功"
    SEND_SUCCESS = "发送成功"
    FORWARD_SUCCESS = "转发成功"
    ADD_SUCCESS = "添加成功"
    COLLECT_SUCCESS = "收藏成功"
    DELETE_SUCCESS = "删除成功"
    SAVED_TO_ALBUM = "已保存到相册"
    COPIED_TO_CLIPBOARD = "已复制到剪贴板"

    # --------------------------------------------------------------------------
    # 3. 群聊与个人资料状态
    # --------------------------------------------------------------------------
    AVATAR_UPDATE_SUCCESS = "头像更新成功"
    GROUP_DISMISS_SUCCESS = "解散成功"
    GROUP_NOT_EXIST = "群不存在"
    GROUP_CREATE_SUCCESS = "创建成功"

    # --------------------------------------------------------------------------
    # 4. 动态 / 朋友圈
    # --------------------------------------------------------------------------
    MOMENT_PUBLISH_SUCCESS = "发布成功"

    # --------------------------------------------------------------------------
    # 5. 表情商店与表情包
    # --------------------------------------------------------------------------
    ALREADY_ADDED = "已添加"
    EMOJI_ALREADY_ADDED = "该表情已添加"

    def for_platform(self, platform: str | None = None) -> str:
        """
        按运行平台返回对应 Toast 文案；未配置平台特例时回退默认文案。
        :param platform: 运行平台名称（如 'android' / 'harmonyos' / 'ios'）
        :return: 适配目标平台的预期 Toast 文本
        """
        platform_key = (platform or "").strip().lower()
        return _PLATFORM_TOAST_OVERRIDES.get((self, platform_key), str(self))


# 仅登记与默认文案不一致的平台特例，避免枚举名出现 _HOS / _IOS 后缀膨胀
_PLATFORM_TOAST_OVERRIDES: dict[tuple[ToastMsg, str], str] = {
    (ToastMsg.SWITCH_NETWORK, "harmonyos"): "请检查网络或SIM卡后重试",
}
