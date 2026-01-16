import aiohttp
import asyncio
import json
import time
import hmac
import hashlib
import urllib.parse as parse
import uuid
import base64

# 请填写你的配置信息
SECRET_ID = "your_secret_id"
SECRET_KEY = "your_secret_key"
APP_ID = 0
SDK_APP_ID = 0

HOST = "flowtts.cloud.tencent.com"


def generate_signature(params):
    """生成签名"""
    sorted_params = sorted(params.items())
    sign_str = f"GET{HOST}/api/v1/flow_tts/bidirection?"
    sign_str += "&".join([f"{k}={v}" for k, v in sorted_params])
    
    signature = hmac.new(SECRET_KEY.encode('utf-8'), sign_str.encode('utf-8'), hashlib.sha1).digest()
    return base64.b64encode(signature).decode('utf-8')


def generate_url():
    """生成WebSocket连接URL"""
    connection_id = str(uuid.uuid4())
    timestamp = int(time.time())
    
    params = {
        "Action": "TextToSpeechBidirection",
        "AppId": APP_ID,
        "SecretId": SECRET_ID,
        "SdkAppId": SDK_APP_ID,
        "Timestamp": timestamp,
        "Expired": timestamp + 86400,
        "ConnectionId": connection_id,
    }
    
    params["Signature"] = generate_signature(params)
    query_string = "&".join([f"{k}={parse.quote(str(v))}" for k, v in sorted(params.items())])
    url = f"wss://{HOST}/api/v1/flow_tts/bidirection?{query_string}"
    
    return url, connection_id


class TTSWebSocketClient:
    def __init__(self):
        self.ws = None
        self.connection_id = None
        self.session_id = None
        self.session = None

    async def connect(self):
        """建立WebSocket连接"""
        url, self.connection_id = generate_url()
        print(f"连接URL: {url}")

        self.session = aiohttp.ClientSession()

        try:
            async with self.session.ws_connect(url) as ws:
                self.ws = ws
                print("WebSocket连接已建立")
                await self.start_session()
                await self.receive_messages()
        except Exception as e:
            print(f"连接错误: {e}")
        finally:
            await self.session.close()

    async def receive_messages(self):
        """接收WebSocket消息"""
        async for msg in self.ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                await self.handle_message(msg.data)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print(f"WebSocket错误: {self.ws.exception()}")
                break
            elif msg.type == aiohttp.WSMsgType.CLOSED:
                print("WebSocket连接已关闭")
                break

    async def handle_message(self, message):
        """处理接收到的消息"""
        msg = json.loads(message)
        event = msg.get("Event")
        print(f"\n收到事件: {event}")

        if event == "SessionStart":
            self.session_id = msg.get("SessionId")
            print(f"会话已开始，SessionId: {self.session_id}")
            asyncio.create_task(self.send_text_stream())

        elif event == "SentenceAudio":
            data = msg.get("Data", {})
            print(f"收到句子: {data.get('Sentence')} (音频: {len(data.get('Audio', ''))} 字符)")

        elif event == "SessionEnd":
            data = msg.get("Data", {})
            print(f"会话结束 - 句子数: {data.get('TotalSentences')}, 时长: {data.get('TotalDuration')}秒")
            await self.ws.close()

        elif event == "SessionError":
            error_data = msg.get("Data", {})
            print(f"会话错误: {error_data.get('ErrorCode')} - {error_data.get('ErrorMessage')}")

        elif event == "SentenceError":
            error_data = msg.get("Data", {})
            print(f"句子错误: {error_data}")

    async def start_session(self):
        """开始会话"""
        message = {
            "Event": "StartSession",
            "ConnectionId": self.connection_id,
            "SessionId": "",
            "MessageId": str(uuid.uuid4()),
            "Data": {
                "Voice": {
                    "VoiceId": "v-male-s5NqE0rZ"
                }
            }
        }

        await self.ws.send_str(json.dumps(message, ensure_ascii=False))
        print("已发送StartSession")

    async def send_text_stream(self):
        """流式发送文本"""
        texts = ["今天天气", "真好！", "你那边", "怎么样？", "我这边阳光明媚。"]

        for i, text in enumerate(texts):
            await asyncio.sleep(1)
            message = {
                "Event": "ContinueSession",
                "ConnectionId": self.connection_id,
                "SessionId": self.session_id,
                "MessageId": str(uuid.uuid4()),
                "Data": {"Text": text}
            }
            await self.ws.send_str(json.dumps(message, ensure_ascii=False))
            print(f"已发送文本 [{i+1}/{len(texts)}]: {text}")

        await asyncio.sleep(1)
        await self.finish_session()

    async def finish_session(self):
        """结束会话"""
        message = {
            "Event": "FinishSession",
            "ConnectionId": self.connection_id,
            "SessionId": self.session_id,
            "MessageId": str(uuid.uuid4()),
            "Data": {}
        }
        await self.ws.send_str(json.dumps(message, ensure_ascii=False))
        print("已发送FinishSession")


async def main():
    client = TTSWebSocketClient()
    await client.connect()


if __name__ == "__main__":
    asyncio.run(main())