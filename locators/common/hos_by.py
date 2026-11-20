"""鸿蒙 NEXT (appium-harmonyos-driver) 原生高速定位表达式构造器。

基于驱动原生支持的 text / type / key / id / HypiumBy (byExpression) 策略，
直接下发设备端 uitest 引擎检索，避免触发全量 ArkUI 控件树转 XML 的 XPath 性能瓶颈。
"""


class HosBy:
    """鸿蒙原生定位器工厂（返回标准 (strategy, value) 二元组，直接兼容 BasePage 与 Appium）。"""

    @staticmethod
    def _escape(value: str) -> str:
        """转义 HypiumBy 表达式字符串中的反斜杠与双引号，避免动态文本注入导致解析失败。"""
        return value.replace("\\", "\\\\").replace('"', '\\"')

    @staticmethod
    def text(value: str) -> tuple[str, str]:
        """按精确文本原生直查（底层对应 BY.text）。"""
        return ("text", value)

    @staticmethod
    def type_only(comp_type: str) -> tuple[str, str]:
        """按 ArkUI 控件类型原生直查（如 Search / Checkbox / List / ListItem）。"""
        return ("type", comp_type)

    @staticmethod
    def key(value: str) -> tuple[str, str]:
        """按 ArkUI 控件 key 原生直查（底层对应 BY.key）。"""
        return ("key", value)

    @staticmethod
    def id_only(value: str) -> tuple[str, str]:
        """按 ArkUI 控件 id 原生直查（底层对应 BY.id）。"""
        return ("id", value)

    @staticmethod
    def expr(expression: str) -> tuple[str, str]:
        """透传自定义 HypiumBy 原生表达式（底层交由 byExpression 执行）。"""
        return ("HypiumBy", expression)

    @classmethod
    def type_text(cls, comp_type: str, text: str) -> tuple[str, str]:
        """按 ArkUI 控件类型 + 精确文本组合直查。"""
        safe_type = cls._escape(comp_type)
        safe_text = cls._escape(text)
        return ("HypiumBy", f'BY.type("{safe_type}").text("{safe_text}")')

    @classmethod
    def type_id(cls, comp_type: str, element_id: str) -> tuple[str, str]:
        """按 ArkUI 控件类型 + 控件 id 组合直查。"""
        safe_type = cls._escape(comp_type)
        safe_id = cls._escape(element_id)
        return ("HypiumBy", f'BY.type("{safe_type}").id("{safe_id}")')

    @classmethod
    def before_text(cls, anchor_text: str, target_type: str = "Image") -> tuple[str, str]:
        """无文本图标定位：按相对顺序定位位于锚点文本之前的指定类型控件。"""
        safe_anchor = cls._escape(anchor_text)
        safe_type = cls._escape(target_type)
        return ("HypiumBy", f'BY.isBefore(BY.text("{safe_anchor}")).type("{safe_type}")')

    @classmethod
    def after_text(cl7s, anchor_text: str, target_type: str = "Image") -> tuple[str, str]:
        """无文本图标定位：按相对顺序定位位于锚点文本之后的指定类型控件。"""
        safe_anchor = cls._escape(anchor_text)
        safe_type = cls._escape(target_type)
        return ("HypiumBy", f'BY.isAfter(BY.text("{safe_anchor}")).type("{safe_type}")')
