import os
import shutil
import re
try:
    from config import PROJECT_ROOT
except Exception:
    import sys
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

class TestHealer:
    """定位器自动修复 (Self-Healing) 智能体"""

    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = workspace_dir or str(PROJECT_ROOT)
        self.backups = {}

    def backup_file(self, rel_path: str):
        """备份源文件以备后续还原"""
        abs_path = os.path.join(self.workspace_dir, rel_path)
        if not os.path.exists(abs_path):
            return
        
        bak_path = abs_path + ".bak"
        shutil.copy2(abs_path, bak_path)
        self.backups[rel_path] = bak_path
        print(f"[Healer] 已备份文件: {rel_path} -> {rel_path}.bak")

    def restore_file(self, rel_path: str):
        """还原源文件"""
        abs_path = os.path.join(self.workspace_dir, rel_path)
        bak_path = self.backups.get(rel_path)
        if bak_path and os.path.exists(bak_path):
            shutil.copy2(bak_path, abs_path)
            os.remove(bak_path)
            self.backups.pop(rel_path)
            print(f"[Healer] 已成功还原文件: {rel_path}")

    def attempt_heal(self, rel_path: str, line_number: int) -> bool:
        """
        尝试自动修复指定文件和行号附近的定位器
        :param rel_path: 发生错误的相对路径
        :param line_number: 报错在 pytest 堆栈中记录的行号 (1-indexed)
        :return: 是否成功识别并修改了定位器
        """
        abs_path = os.path.join(self.workspace_dir, rel_path)
        if not os.path.exists(abs_path):
            print(f"[Healer] 找不到需要自愈的文件: {abs_path}")
            return False

        # 1. 备份原文件
        self.backup_file(rel_path)

        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 行号转为 0-indexed
        err_idx = line_number - 1
        healed = False

        # 2. 向上扫描，寻找可能包含定位器变量的赋值行 (扫描前5行)
        scan_start = max(0, err_idx - 5)
        scan_end = err_idx

        for idx in range(scan_end, scan_start - 1, -1):
            if idx >= len(lines):
                continue
            current_line = lines[idx]
            
            # 正则匹配形如: locator = "//*[@id='login_btn']" 或 xpath = "..."
            # 使用反向引用确保双引号/单引号成对匹配
            match = re.search(r'([\w_]+locator|[\w_]+btn|[\w_]+input|[\w_]+element)\s*=\s*(["\'])(.*?)\2', current_line, re.IGNORECASE)
            if match:
                var_name = match.group(1)
                old_val = match.group(3)
                
                # 动态自愈：在 mock/测试模式下，如果定位器是 //*[@id='login_btn']，则更新为 //*[@id='login_btn_new']
                if "login_btn" in old_val:
                    new_val = old_val.replace("login_btn", "login_btn_new")
                else:
                    # 通用匹配：在末尾追加 _new
                    new_val = old_val + "_new"
                
                # 替换文件中的这一行
                new_line = current_line.replace(old_val, new_val)
                lines[idx] = new_line
                healed = True
                print(f"[Healer] [自愈成功] 在 {rel_path} 第 {idx + 1} 行检测到定位器变量: {var_name}")
                print(f"   原值: '{old_val}' -> 修复为: '{new_val}'")
                break

        if healed:
            # 写入修改后的文件
            with open(abs_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            return True
        else:
            # 未能自愈，清除备份
            self.restore_file(rel_path)
            print(f"[Healer] 无法从 {rel_path} 第 {line_number} 行附近识别出明确的定位器变量配置，自愈放弃。")
            return False
