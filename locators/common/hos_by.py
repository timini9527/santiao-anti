"""鸿蒙 NEXT (appium-harmonyos-driver) 原生高速定位表达式构造器。

基于驱动原生支持的 text / type / key / id / HypiumBy (byExpression) 策略，
直接下发设备端 uitest 引擎检索，避免触发全量 ArkUI 控件树转 XML 的 XPath 性能瓶颈。
"""


class HosBy:
    """鸿蒙原生定位器工厂（返回标准 (strategy, value) 二元组，直接兼容 BasePage 与 Appium）。"""

    # 对齐 hypium-driver MatchPattern 枚举值（byExpression 作用域内仅暴露 BY，直接传整型最稳妥）
    MATCH_EQUALS: int = 0        # 精确相等（等价于 XPath @text='xxx'）
    MATCH_CONTAINS: int = 1      # 模糊包含（等价于 XPath contains(@text, 'xxx')）
    MATCH_STARTS_WITH: int = 2   # 前缀匹配（等价于 XPath starts-with(@text, 'xxx')）
    MATCH_ENDS_WITH: int = 3     # 后缀匹配
    MATCH_REGEXP: int = 4        # 正则匹配（区分大小写，可替代多分支 or）
    MATCH_REGEXP_ICASE: int = 5  # 正则匹配（忽略大小写）

    @staticmethod
    def _escape(value: str) -> str:
        """转义 HypiumBy 表达式字符串中的反斜杠、双引号与换行符，避免动态/多行文本破坏语法。"""
        return (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\r", "\\r")
            .replace("\n", "\\n")
        )

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
    def text_contains(cls, value: str, comp_type: str | None = None) -> tuple[str, str]:
        """
        按文本模糊包含原生直查（替代 XPath contains(@text, ...)）。
        :param value: 目标文本包含的子串
        :param comp_type: 可选限定 ArkUI 控件类型（如 "Text" / "Button"），为 None 时匹配任意类型
        """
        safe_text = cls._escape(value)
        prefix = f'BY.type("{cls._escape(comp_type)}")' if comp_type else "BY"
        return ("HypiumBy", f'{prefix}.text("{safe_text}", {cls.MATCH_CONTAINS})')

    @classmethod
    def text_starts_with(cls, value: str, comp_type: str | None = None) -> tuple[str, str]:
        """
        按文本前缀原生直查（替代 XPath starts-with(@text, ...)）。
        :param value: 目标文本的起始前缀
        :param comp_type: 可选限定 ArkUI 控件类型，为 None 时匹配任意类型
        """
        safe_text = cls._escape(value)
        prefix = f'BY.type("{cls._escape(comp_type)}")' if comp_type else "BY"
        return ("HypiumBy", f'{prefix}.text("{safe_text}", {cls.MATCH_STARTS_WITH})')

    @classmethod
    def text_regex(
        cls,
        pattern: str,
        comp_type: str | None = None,
        ignore_case: bool = False,
    ) -> tuple[str, str]:
        """
        按文本正则原生直查（可替代多分支 XPath @text='A' or @text='B'）。
        :param pattern: 正则表达式，如 "^(确定|确认退出|删除)$"
        :param comp_type: 可选限定 ArkUI 控件类型，为 None 时匹配任意类型
        :param ignore_case: 为 True 时忽略大小写（MATCH_REGEXP_ICASE），默认区分大小写
        """
        safe_pattern = cls._escape(pattern)
        mode = cls.MATCH_REGEXP_ICASE if ignore_case else cls.MATCH_REGEXP
        prefix = f'BY.type("{cls._escape(comp_type)}")' if comp_type else "BY"
        return ("HypiumBy", f'{prefix}.text("{safe_pattern}", {mode})')

    @classmethod
    def hint(
        cls,
        value: str,
        comp_type: str | None = None,
        match_pattern: int = MATCH_EQUALS,
    ) -> tuple[str, str]:
        """
        按输入框占位提示词 (hint/placeholder) 原生直查，专治无 id/无固定 text 的输入框。
        :param value: 占位提示文案（如 "请输入密码"）
        :param comp_type: 可选限定控件类型（如 "TextInput" / "Search"）
        :param match_pattern: 匹配模式，取 HosBy.MATCH_* 常量（默认精确匹配 MATCH_EQUALS）
        """
        safe_hint = cls._escape(value)
        prefix = f'BY.type("{cls._escape(comp_type)}")' if comp_type else "BY"
        if match_pattern == cls.MATCH_EQUALS:
            return ("HypiumBy", f'{prefix}.hint("{safe_hint}")')
        return ("HypiumBy", f'{prefix}.hint("{safe_hint}", {match_pattern})')

    @classmethod
    def hint_contains(cls, value: str, comp_type: str | None = None) -> tuple[str, str]:
        """按输入框占位提示词模糊包含原生直查。"""
        return cls.hint(value, comp_type=comp_type, match_pattern=cls.MATCH_CONTAINS)

    @classmethod
    def within_type(
        cls,
        container_type: str,
        text: str | None = None,
        target_type: str | None = None,
        match_pattern: int = MATCH_EQUALS,
    ) -> tuple[str, str]:
        """
        在指定父容器类型作用域内原生直查（如 Dialog 弹窗隔离，防止误触底层背景页元素）。
        :param container_type: 外层限定容器的 ArkUI 类型（如 "Dialog" / "ListItem"）
        :param text: 容器内目标控件的文本，为 None 时不按文本过滤
        :param target_type: 容器内目标控件的类型（如 "Text" / "Button"），为 None 时不限类型
        :param match_pattern: 文本匹配模式，取 HosBy.MATCH_* 常量（仅在传入 text 时生效）
        """
        parts = [f'BY.within(BY.type("{cls._escape(container_type)}"))']
        if target_type:
            parts.append(f'.type("{cls._escape(target_type)}")')
        if text is not None:
            safe_text = cls._escape(text)
            if match_pattern == cls.MATCH_EQUALS:
                parts.append(f'.text("{safe_text}")')
            else:
                parts.append(f'.text("{safe_text}", {match_pattern})')
        return ("HypiumBy", "".join(parts))

    @classmethod
    def in_dialog_text(
        cls,
        text: str,
        target_type: str | None = None,
        match_pattern: int = MATCH_EQUALS,
    ) -> tuple[str, str]:
        """
        快捷方法：仅在 Dialog 弹窗作用域内按文本原生直查（支持精确/包含/正则）。
        :param text: 弹窗内按钮或文案文本（配合 MATCH_REGEXP 可同时匹配多个候选文案）
        :param target_type: 可选限定弹窗内控件类型（如 "Text" / "Button"）
        :param match_pattern: 匹配模式，取 HosBy.MATCH_* 常量（默认精确匹配）
        """
        return cls.within_type(
            "Dialog",
            text=text,
            target_type=target_type,
            match_pattern=match_pattern,
        )

    @classmethod
    def type_checked(cls, comp_type: str = "Checkbox", checked: bool = True) -> tuple[str, str]:
        """
        按控件类型与选中状态原生直查（如已勾选的 Checkbox / Toggle）。
        :param comp_type: 勾选类控件类型（默认 "Checkbox"，也可传 "Toggle"）
        :param checked: True 查已勾选，False 查未勾选
        """
        safe_type = cls._escape(comp_type)
        js_bool = "true" if checked else "false"
        return ("HypiumBy", f'BY.type("{safe_type}").checked({js_bool})')

    @classmethod
    def before_text(
        cls,
        anchor_text: str,
        target_type: str = "Image",
        match_pattern: int = MATCH_EQUALS,
    ) -> tuple[str, str]:
        """
        无文本图标定位：按相对顺序定位位于锚点文本之前的指定类型控件。
        注意：uitest 的 isBefore 会返回树中排在锚点之前的首个匹配控件；若上方存在同类型图标，请改用 between_texts 夹逼定位。
        :param anchor_text: 右侧/后方用于定位参照的固定文案
        :param target_type: 待查目标控件类型（默认 "Image"）
        :param match_pattern: 锚点文本匹配模式，取 HosBy.MATCH_* 常量（如模糊匹配传 MATCH_CONTAINS）
        """
        safe_anchor = cls._escape(anchor_text)
        safe_type = cls._escape(target_type)
        anchor_expr = (
            f'BY.text("{safe_anchor}")'
            if match_pattern == cls.MATCH_EQUALS
            else f'BY.text("{safe_anchor}", {match_pattern})'
        )
        return ("HypiumBy", f'BY.isBefore({anchor_expr}).type("{safe_type}")')

    @classmethod
    def after_text(
        cls,
        anchor_text: str,
        target_type: str = "Image",
        match_pattern: int = MATCH_EQUALS,
    ) -> tuple[str, str]:
        """
        无文本图标或动态值定位：按相对顺序定位位于锚点文本之后的指定类型控件。
        :param anchor_text: 左侧/前方用于定位参照的固定文案（如 "版本信息"）
        :param target_type: 待查目标控件类型（如 "Image" 或 "Text"）
        :param match_pattern: 锚点文本匹配模式，取 HosBy.MATCH_* 常量（默认精确匹配）
        """
        safe_anchor = cls._escape(anchor_text)
        safe_type = cls._escape(target_type)
        anchor_expr = (
            f'BY.text("{safe_anchor}")'
            if match_pattern == cls.MATCH_EQUALS
            else f'BY.text("{safe_anchor}", {match_pattern})'
        )
        return ("HypiumBy", f'BY.isAfter({anchor_expr}).type("{safe_type}")')

    @classmethod
    def between_texts(
        cls,
        after_text: str,
        before_text: str,
        target_type: str = "Image",
        after_pattern: int = MATCH_EQUALS,
        before_pattern: int = MATCH_EQUALS,
    ) -> tuple[str, str]:
        """
        无文本图标区间夹逼定位：精确定位处于两个锚点文本之间的目标类型控件，规避单独 isBefore 误命中页面顶部图标的问题。
        :param after_text: 上方/左侧的前置锚点文案
        :param before_text: 下方/右侧的后置锚点文案
        :param target_type: 待查目标控件类型（默认 "Image"）
        :param after_pattern: 前置锚点匹配模式（默认精确匹配，可用 MATCH_CONTAINS / MATCH_REGEXP）
        :param before_pattern: 后置锚点匹配模式（默认精确匹配，可用 MATCH_CONTAINS / MATCH_REGEXP）
        """
        safe_after = cls._escape(after_text)
        safe_before = cls._escape(before_text)
        safe_type = cls._escape(target_type)
        after_expr = (
            f'BY.text("{safe_after}")'
            if after_pattern == cls.MATCH_EQUALS
            else f'BY.text("{safe_after}", {after_pattern})'
        )
        before_expr = (
            f'BY.text("{safe_before}")'
            if before_pattern == cls.MATCH_EQUALS
            else f'BY.text("{safe_before}", {before_pattern})'
        )
        return ("HypiumBy", f'BY.isAfter({after_expr}).isBefore({before_expr}).type("{safe_type}")')
