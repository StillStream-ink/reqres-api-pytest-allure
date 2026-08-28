# common/feishu_notify.py
import requests
import json
import sys
import os

# 从环境变量读取 Webhook 地址，方便在不同环境切换
WEBHOOK_URL = os.environ.get("FEISHU_WEBHOOK", "https://open.feishu.cn/open-apis/bot/v2/hook/9bdcd568-c176-4fe6-acd3-d69d4177129e")

def send_feishu_message(title, content, status="success"):
    """
    发送飞书消息
    :param title: 消息标题
    :param content: 消息内容
    :param status: 状态，success 或 failure，用于显示不同颜色的标题
    """
    if not WEBHOOK_URL or WEBHOOK_URL == "请在这里粘贴你的完整 Webhook 地址":
        print("⚠️ 警告：未配置飞书 Webhook，消息未发送")
        return False

    # 根据状态选择颜色
    color = "green" if status == "success" else "red"
    # 构建卡片消息
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": content,
                        "tag": "lark_md"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "content": f"🏷️ 项目: reqres_api_test",
                            "tag": "plain_text"
                        }
                    ]
                }
            ],
            "header": {
                "title": {
                    "content": title,
                    "tag": "plain_text"
                },
                "template": color
            }
        }
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=5)
        if response.status_code == 200 and response.json().get("StatusCode") == 0:
            print("✅ 飞书消息发送成功")
            return True
        else:
            print(f"❌ 飞书消息发送失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 发送飞书消息异常: {e}")
        return False