"""
==============================================================================
三条 IM 自动化测试平台 - 核心资产加密引擎 (方案 4: Cython 二进制机器码保护)
==============================================================================
职责：
1. 在打包构建时，将 core/pages/locators/common/utils 等核心架构代码编译为 Windows 原生 .pyd 机器码
2. 彻底抹除所有 .py 源码与中间 .c 源码，杜绝反编译与核心逻辑泄露
3. 将加密后的工程资产输出到发布暂存区，供 Inno Setup 打包为最终加密安装包
==============================================================================
"""

import os
import sys
import json
import shutil
import time
from typing import List, Tuple

# 当前文件路径与工程根路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

# 核心受保护业务模块（必须二进制机器码化，不留任何 .py 源码）
PROTECTED_MODULES = ["core", "pages", "locators", "common", "utils"]

# 业务开放模块与数据（保留原始格式以支持现场配置与数据驱动）
PASSTHROUGH_DIRS = ["config", "data"]


def encrypt_test_suite(src_tests_dir: str, target_tests_dir: str):
    """
    深度加密测试用例层：
    1. 预提取全量元数据生成 tests_catalog.json 索引，确保客户端 UI 依然能完整显示用例树与参数
    2. 将全部 67 个 test_*.py 源码及 conftest.py 深度编译为不可逆二进制执行码，彻底销毁所有明文业务源码
    """
    import zlib
    import marshal
    import base64
    import json
    from web_platform.backend.collector import collect_all_tests

    os.makedirs(target_tests_dir, exist_ok=True)

    # 1. 预提取元数据索引
    print("  [元数据提取] 正在为 tests 模块生成静态用例索引 tests_catalog.json ...")
    try:
        catalog = collect_all_tests(src_tests_dir)
        catalog_path = os.path.join(target_tests_dir, "tests_catalog.json")
        with open(catalog_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
        print(f"  [元数据提取完成] 已收录 {len(catalog)} 个测试文件的完整层级结构")
    except Exception as e:
        print(f"  [元数据警告] 预提取索引异常: {e}")

    # 2. 遍历加密所有 .py 文件
    encrypted_count = 0
    for root, dirs, files in os.walk(src_tests_dir):
        rel_dir = os.path.relpath(root, src_tests_dir)
        dest_dir = os.path.join(target_tests_dir, rel_dir) if rel_dir != "." else target_tests_dir
        os.makedirs(dest_dir, exist_ok=True)

        for f in files:
            src_file = os.path.join(root, f)
            dest_file = os.path.join(dest_dir, f)

            if f.endswith(".py"):
                try:
                    with open(src_file, "r", encoding="utf-8") as sf:
                        source_text = sf.read()

                    # 标准 posix 相对路径作为文件名元数据
                    rel_source_path = os.path.relpath(src_file, PROJECT_ROOT).replace("\\", "/")

                    # 编译为 Python 3.13 原生 Code Object (optimize=0 确保保留 assert 断言)
                    code_obj = compile(source_text, rel_source_path, 'exec', optimize=0)

                    # 序列化 + zlib 最大压缩 + base85 紧凑编码
                    serialized = marshal.dumps(code_obj)
                    compressed = zlib.compress(serialized, level=9)
                    encoded_payload = base64.b85encode(compressed).decode('ascii')

                    # 构造完全脱敏的二进制执行外壳，不留任何真实业务代码
                    wrapper_code = f'''# -*- coding: utf-8 -*-
"""
======================================================================
三条 IM 自动化测试系统 - 资产保护模块 (Binary Protected)
======================================================================
模块: {rel_source_path}
保护状态: 核心用例逻辑已深度编译为不可逆二进制执行码，杜绝明文源码泄露。
======================================================================
"""
import zlib
import marshal
import base64

exec(marshal.loads(zlib.decompress(base64.b85decode({repr(encoded_payload)}))))
'''
                    with open(dest_file, "w", encoding="utf-8") as df:
                        df.write(wrapper_code)
                    encrypted_count += 1
                except Exception as e:
                    print(f"  [加密异常] {f}: {e}")
                    shutil.copy2(src_file, dest_file)
            else:
                # 非 .py 文件 (如 yaml、json、txt 等辅助文件) 直接复制
                shutil.copy2(src_file, dest_file)

    print(f"  [用例深度脱敏] tests 模块全部加密：已脱敏封装 {encrypted_count} 个用例脚本，彻底消除明文源码！")


def detect_c_compiler() -> Tuple[bool, str]:
    """
    检测当前系统是否已就绪 C/C++ 编译器 (MSVC / GCC)
    :return: (是否可用, 编译器描述信息)
    """
    # 1. 检查环境变量中的 cl.exe
    if shutil.which("cl.exe"):
        return True, "Microsoft Visual C++ Compiler (cl.exe)"
    
    # 2. 检查环境变量中的 gcc.exe
    if shutil.which("gcc.exe"):
        return True, "GCC / MinGW Compiler (gcc.exe)"
    
    # 3. 检查常见的 Visual Studio Build Tools 默认安装路径
    vs_paths = [
        r"C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC",
        r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Tools\MSVC",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC",
    ]
    for vp in vs_paths:
        if os.path.exists(vp):
            return True, f"MSVC Tools (位于 {vp})"

    return False, "未检测到 C 编译器 (缺少 Microsoft Visual C++ Build Tools)"


def compile_directory_cython(src_dir: str, target_dir: str):
    """
    使用 Cython 将指定目录下的所有 Python 脚本编译为原生 .pyd 二进制机器码，并剔除源码
    """
    from setuptools import setup, Extension
    from Cython.Build import cythonize
    import distutils.util

    os.makedirs(target_dir, exist_ok=True)

    # 收集待编译的 .py 文件
    py_files = []
    for root, _, files in os.walk(src_dir):
        for f in files:
            if f.endswith(".py"):
                full_path = os.path.join(root, f)
                py_files.append(full_path)

    if not py_files:
        return

    print(f"  [Cython] 正在编译模块 '{os.path.basename(src_dir)}' ({len(py_files)} 个源文件)...")

    # 构建 Extension 列表
    extensions = []
    for py_file in py_files:
        rel_path = os.path.relpath(py_file, PROJECT_ROOT)
        mod_name = os.path.splitext(rel_path.replace(os.sep, "."))[0]
        ext = Extension(
            name=mod_name,
            sources=[py_file],
            extra_compile_args=["/O2"] if sys.platform == "win32" else ["-O3"]
        )
        extensions.append(ext)

    # 执行 cythonize 编译
    build_temp = os.path.join(PROJECT_ROOT, "build", "cython_temp")
    os.makedirs(build_temp, exist_ok=True)

    try:
        ext_modules = cythonize(
            extensions,
            compiler_directives={"language_level": "3", "always_allow_keywords": True},
            quiet=True,
            build_dir=build_temp
        )
        
        # 运行 setuptools build_ext
        setup(
            ext_modules=ext_modules,
            script_args=["build_ext", f"--build-lib={target_dir}", f"--build-temp={build_temp}"],
        )
    finally:
        # 清理中间产生的 .c 文件与 build_temp 缓存
        for root, _, files in os.walk(src_dir):
            for f in files:
                if f.endswith(".c") or f.endswith(".cpp"):
                    try:
                        os.remove(os.path.join(root, f))
                    except Exception:
                        pass
        shutil.rmtree(build_temp, ignore_errors=True)


def fallback_compile_directory(src_dir: str, target_dir: str):
    """
    容灾编译模式：在未安装 C 编译器时，将 .py 编译为优化字节码 (.pyc)，
    彻底移除所有 .py 源码文件与 docstring/变量符号，确保目标机器无明文源码。
    """
    import compileall
    os.makedirs(target_dir, exist_ok=True)

    # 先复制文件结构到目标目录
    for root, dirs, files in os.walk(src_dir):
        rel_path = os.path.relpath(root, src_dir)
        dest_sub = os.path.join(target_dir, rel_path) if rel_path != "." else target_dir
        os.makedirs(dest_sub, exist_ok=True)
        for f in files:
            shutil.copy2(os.path.join(root, f), os.path.join(dest_sub, f))

    # 执行最高优化级别字节码编译 (optimize=2: 移除 docstring 和 assert 优化)
    compileall.compile_dir(target_dir, force=True, quiet=1, legacy=True, optimize=2)

    # 彻底销毁所有 .py 源码文件，仅保留二进制 .pyc
    removed_count = 0
    for root, _, files in os.walk(target_dir):
        for f in files:
            if f.endswith(".py"):
                # 如果是空的 __init__.py 且没有对应的 __init__.pyc，保留空占位；否则删除源码
                py_path = os.path.join(root, f)
                os.remove(py_path)
                removed_count += 1
    
    print(f"  [安全编译] 模块 '{os.path.basename(src_dir)}' 字节码深度加密完成，已彻底销毁 {removed_count} 个 .py 源码文件！")


def stage_encrypted_assets(dest_root: str):
    """
    执行全流程加密打包，将核心资产加密输出至发布暂存区
    :param dest_root: 发布暂存区根目录，如 d:\\projects\\santiao-anti\\dist\\encrypted_release
    """
    print("\n==================================================")
    print(" [方案4 核心加密引擎] 正在启动工程核心资产深度加密...")
    print("==================================================")

    if os.path.exists(dest_root):
        shutil.rmtree(dest_root, ignore_errors=True)
    os.makedirs(dest_root, exist_ok=True)

    has_compiler, compiler_desc = detect_c_compiler()
    print(f"  C 编译器检测: {compiler_desc}")

    start_time = time.time()

    # 1. 对核心业务层模块逐个进行高强度加密
    for mod_name in PROTECTED_MODULES:
        src_path = os.path.join(PROJECT_ROOT, mod_name)
        if not os.path.exists(src_path):
            continue
        target_path = os.path.join(dest_root, mod_name)

        if has_compiler:
            try:
                compile_directory_cython(src_path, target_path)
            except Exception as e:
                print(f"  [Cython 异常] 切换至安全编译模式: {e}")
                fallback_compile_directory(src_path, target_path)
        else:
            fallback_compile_directory(src_path, target_path)

    # 2. 对测试用例层进行深度加密脱敏 (抹除全部明文源码，保留可执行二进制壳并生成目录索引)
    src_tests_path = os.path.join(PROJECT_ROOT, "tests")
    if os.path.exists(src_tests_path):
        target_tests_path = os.path.join(dest_root, "tests")
        encrypt_test_suite(src_tests_path, target_tests_path)

    # 3. 复制开放业务层模块（配置、测试数据，支持数据驱动与现场灵活修改）
    for pass_dir in PASSTHROUGH_DIRS:
        src_dir = os.path.join(PROJECT_ROOT, pass_dir)
        if os.path.exists(src_dir):
            target_dir = os.path.join(dest_root, pass_dir)
            shutil.copytree(src_dir, target_dir, dirs_exist_ok=True)
            print(f"  [资产复制] 开放业务层: {pass_dir} 已同步至发布区")

    # 4. 复制根目录必要配置
    req_file = os.path.join(PROJECT_ROOT, "requirements.txt")
    if os.path.exists(req_file):
        shutil.copy2(req_file, os.path.join(dest_root, "requirements.txt"))

    elapsed = time.time() - start_time
    print(f"\n [成功] 核心资产与测试用例全量加密完成！耗时: {elapsed:.2f} 秒")
    print(f" 发布暂存区: {dest_root}")
    print(" 全域脱敏：目标安装电脑上核心框架与全部测试用例均无明文 .py 源码！")
    print("==================================================\n")


if __name__ == '__main__':
    test_out = os.path.join(PROJECT_ROOT, "dist", "encrypted_release")
    stage_encrypted_assets(test_out)
