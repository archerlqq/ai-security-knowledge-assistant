import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# 显式指定 .env 位置：默认的 load_dotenv() 只查当前工作目录，
# 从其他目录启动时会读不到密钥，误判为"未配置"。
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DIFY_API_URL = os.getenv("DIFY_API_URL", "https://api.dify.ai/v1/chat-messages")
DIFY_USER_ID = os.getenv("DIFY_USER_ID", "demo-user")

def call_dify_api(query: str) -> dict:
    if not DIFY_API_KEY:
        return {
            "success": False,
            "answer": "",
            "error": "未配置 DIFY_API_KEY，请检查 .env 文件。"
        }

    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": {},
        "query": query,
        "response_mode": "blocking",
        "conversation_id": "",
        "user": DIFY_USER_ID
    }

    try:
        response = requests.post(
            DIFY_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            return {
                "success": False,
                "answer": "",
                "error": f"Dify API 请求失败，状态码：{response.status_code}，返回内容：{response.text[:300]}"
            }

        data = response.json()
        answer = data.get("answer", "")

        if not answer:
            return {
                "success": False,
                "answer": "",
                "error": "Dify API 返回成功，但未找到 answer 字段。"
            }

        return {
            "success": True,
            "answer": answer,
            "error": ""
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "answer": "",
            "error": "Dify API 请求超时，请稍后重试。"
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "answer": "",
            "error": f"Dify API 网络请求异常：{e}"
        }

    except ValueError:
        return {
            "success": False,
            "answer": "",
            "error": "Dify API 返回内容不是合法 JSON。"
        }