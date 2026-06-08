import sys
import os

try:
    from openai import OpenAI
    print("成功导入 OpenAI 模块")
except ImportError:
    print("错误: 未安装 'openai' 模块。请运行 'pip install openai' 进行安装。")
    sys.exit(1)

# NVIDIA API 配置
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"
)

try:
    model="z-ai/glm-5.1"
        # deepseek-ai/deepseek-v3.2
        # moonshotai/kimi-k2.5
        # moonshotai/kimi-k2-thinking
        # minimaxai/minimax-m2.7
        # z-ai/glm-5.1
        # google/gemma-4-31b
        # meta/llama-4-scout-17b-16e-instruc
    print(f"正在发起 API 请求 (模型: {model})...")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": "你好，介绍一下你自己"}
        ],
        max_tokens=1024
    )

    print("请求已完成。")
    if response and response.choices:
        content = response.choices[0].message.content
        if content:
            print("--- 响应内容 ---")
            print(content)
        else:
            print("警告: 响应内容为空。")
    else:
        print("错误: API 返回了无效的响应格式。")

except Exception as e:
    print(f"调用 API 时发生错误: {type(e).__name__}: {e}")