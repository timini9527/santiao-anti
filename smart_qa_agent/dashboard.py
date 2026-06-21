import os
import sys
import io
import streamlit as st
from contextlib import redirect_stdout

# 确保能正确导入同包内的模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.append(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from smart_executor import SmartExecutor

# 配置 Streamlit 页面属性 (Wow Aesthetics)
st.set_page_config(
    page_title="Smart QA Control Center",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 注入 CSS 提升视觉高级感 (磨砂玻璃与渐变)
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FF4B4B, #FF8E53);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- 侧边栏配置 -----------------
st.sidebar.title("⚙️ 智能控制台配置")
st.sidebar.markdown("---")

st.sidebar.subheader("📝 AI 根因诊断 (RCA) 配置")
ai_key = st.sidebar.text_input("AI API Key", value="sk-MalT0UWMS4qKOhWlKeSqnrgR36DMAKBXO4qL5xE0ZKjOT41P", type="password", help="留空将自动运行在本地规则诊断(Mock)模式")
ai_base = st.sidebar.text_input("AI Base URL", value="https://www.packyapi.com/v1")
ai_model = st.sidebar.text_input("AI Model", value="gpt-5.5")

# 动态注入环境变量
if ai_key:
    os.environ["AI_API_KEY"] = ai_key
    os.environ["AI_BASE_URL"] = ai_base
    os.environ["AI_MODEL"] = ai_model
else:
    # 清理环境变量，保证退回到 Mock 模式
    os.environ.pop("AI_API_KEY", None)

st.sidebar.markdown("---")
st.sidebar.subheader("📊 缺陷平台配置")
st.sidebar.info("⚠️ JIRA 提单通道已由系统全局注释屏蔽，暂时不执行外部对接操作。")

# ----------------- 主界面 -----------------
st.markdown("<div class='main-title'>🤖 IM 自动化测试智能执行与自愈诊断中心</div>", unsafe_allow_html=True)
st.write("欢迎使用可视化测试控制台。在此您可以一键执行测试目标，并实时获取大模型错误诊断与代码自愈结果。")

test_target = st.text_input(
    "🎯 请选择或输入要运行的测试目标（文件/目录）",
    value="smart_qa_agent/tests/test_mock_failures.py"
)

# 占位符定义
log_placeholder = st.empty()
stats_placeholder = st.empty()
report_placeholder = st.empty()

if st.button("🚀 启动智能测试流", use_container_width=True):
    with st.spinner("正在启动自动化测试并执行自愈诊断..."):
        # 1. 拦截 stdout 捕获执行过程日志
        f = io.StringIO()
        executor = SmartExecutor()
        
        try:
            with redirect_stdout(f):
                results = executor.run_smart_workflow(test_target)
            
            # 2. 渲染 Pytest 实况日志
            log_placeholder.markdown("### 📋 自动化测试执行实况")
            log_placeholder.code(f.getvalue(), language="text")
            
            # 3. 统计指标数据
            healed_count = sum(1 for fail in results["failures_details"] if fail.get("healed"))
            
            stats_placeholder.markdown("### 📊 测试结果指标大盘")
            col1, col2, col3, col4 = stats_placeholder.columns(4)
            with col1:
                st.metric("总用例数", results["total"])
            with col2:
                st.metric("通过数 (Passed)", results["passed"], delta_color="normal")
            with col3:
                st.metric("失败数 (Failed)", results["failed"], delta=f"-{results['failed']}" if results["failed"] > 0 else None, delta_color="inverse")
            with col4:
                st.metric("自愈成功数", healed_count, delta=f"+{healed_count}" if healed_count > 0 else None)
                
            # 4. 展示详细诊断卡片
            if results["failed"] > 0:
                report_placeholder.markdown("### 🔴 异常用例 AI RCA 诊断与修复状态")
                
                for fail in results["failures_details"]:
                    is_healed = fail.get("healed", False)
                    status_emoji = "✅ [已成功自愈]" if is_healed else "❌ [自愈失败/未执行]"
                    
                    with report_placeholder.expander(f"{status_emoji} 用例: {fail['file']}::{fail['name']} (第 {fail['line']} 行)"):
                        st.markdown(f"**异常类别**: `{fail['error_class']}`")
                        st.error(f"异常信息: {fail['message']}")
                        
                        st.markdown("#### 🤖 AI 智能诊断分析")
                        st.info(fail.get("rca_report", "暂无分析报告"))
                        
                        if is_healed:
                            st.success("✅ 状态：定位器错误已通过 `TestHealer` 成功自愈！新的定位器已重跑通过，备份文件已安全还原。")
                        else:
                            st.warning("⚠️ 状态：用例最终执行失败。Jira 通道已注释关闭，请手动根据诊断报告排查脚本或被测应用。")
            else:
                st.success("🎉 恭喜！当前运行的测试目标全部通过！没有检测到任何异常。")
                
        except Exception as e:
            st.error(f"执行过程发生严重错误: {e}")
            st.code(f.getvalue(), language="text")
