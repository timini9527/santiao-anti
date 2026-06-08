import requests
import json


def chat_with_agent(text: str = ""):
    # 1. 设置请求的 URL
    url = "http://27.155.82.53:8889/v3/chat"
    # url = "http://27.155.82.53:8889/v3/conversation/create'"

    # 2. 设置请求头 (Headers)
    headers = {
        "Authorization": "Bearer pat_8a9b3799d80095f0a9aaef5b7c8201691ed838c2eaf31ad19b3449eea139eee0",
        "Content-Type": "application/json"
    }

    # 3. 设置请求体数据 (Payload)
    payload = {
        "bot_id": "7622660333416480768",
        "user_id": "12121221122",
        "stream": True,
        "auto_save_history": True,
        "additional_messages": [
            {
                "role": "user",
                "content": f"{text}",
                "content_type": "text"
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, stream=True)
        response.raise_for_status()

        current_event = None
        follow_ups = []

        for line in response.iter_lines():
            if not line:
                continue

            decoded_line = line.decode('utf-8')

            if decoded_line.startswith("event:"):
                current_event = decoded_line.split(":", 1)[1].strip()

            elif decoded_line.startswith("data:"):
                data_str = decoded_line[5:].strip()

                if not data_str or data_str == "[DONE]":
                    continue

                try:
                    data = json.loads(data_str)

                    if current_event == "conversation.message.completed":
                        msg_type = data.get("type")

                        if msg_type == "answer":
                            content = data.get("content")
                            print(f"\n 🤖 Agent 回复:\n {content}")
                            time_cost = data.get("meta_data", {}).get("awaiting", 0)
                            print(f"\n [耗时: {time_cost}s]")

                        elif msg_type == "follow_up":
                            follow_ups.append(data.get("content"))

                except json.JSONDecodeError:
                    pass

        if follow_ups:
            print("\n💡 你可以继续这样问:")
            for i, question in enumerate(follow_ups, 1):
                print(f"  {i}. {question}")
        print("\n" + "=" * 50 + "\n")

    except requests.exceptions.RequestException as e:
        print(f"\n请求发生错误: {e}")

if __name__ == "__main__":
    print("=== 开始聊天🤔🤔🤔🤔🤔🤔🤔🤔🤔🤔 (输入 'exit' 退出) ===")
    while True:
        chat_w = input("\n 请输入问题：\n")

        if chat_w.strip().lower() == "exit":
            print("已退出聊天😒😒😒😒😒😒😒😒😒😒")
            break
        if not chat_w.strip():
            continue

        chat_with_agent(chat_w)
