import os
import aiohttp
import asyncio
import json
import time
import hmac
import hashlib
import struct
import urllib.parse as parse
import uuid
import base64
from dotenv import load_dotenv

load_dotenv()

SECRET_ID = os.getenv("TENCENTCLOUD_SECRET_ID", "your_secret_id")
SECRET_KEY = os.getenv("TENCENTCLOUD_SECRET_KEY", "your_secret_key")
SDK_APP_ID = int(os.getenv("TENCENTCLOUD_SDK_APP_ID") or os.getenv("SDKAPPID") or "0")

HOST = "flowtts.cloud.tencent.com"

# TTS 模型：留空使用服务端默认（flow_02_turbo），也可显式指定
MODEL = os.getenv("FLOW_TTS_MODEL", "flow_02_turbo")
VOICE_ID = os.getenv("FLOW_TTS_VOICE_ID", "v-male-s5NqE0rZ")

# 音频格式：pcm / mp3 / opus（opus 为 Ogg 封装，每句一条独立 Ogg 流）
AUDIO_FORMAT = os.getenv("FLOW_TTS_FORMAT", "pcm")
SAMPLE_RATE = int(os.getenv("FLOW_TTS_SAMPLE_RATE", "24000"))
BIT_RATE = int(os.getenv("FLOW_TTS_BITRATE", "128"))  # 仅 mp3 生效

# 保存文件的扩展名：pcm 会补上 WAV 头，opus 保存为 .ogg
FILE_EXT = {"pcm": "wav", "mp3": "mp3", "opus": "ogg"}


def pcm_to_wav(pcm: bytes, sample_rate: int, channels: int = 1, bits: int = 16) -> bytes:
    """给裸 PCM 数据补上 WAV 头"""
    byte_rate = sample_rate * channels * bits // 8
    block_align = channels * bits // 8
    header = b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt "
    header += struct.pack("<IHHIIHH", 16, 1, channels, sample_rate, byte_rate, block_align, bits)
    header += b"data" + struct.pack("<I", len(pcm))
    return header + pcm


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
        "SecretId": SECRET_ID,
        "SdkAppId": SDK_APP_ID,
        "Timestamp": timestamp,
        "Expired": timestamp + 86400,
        "ConnectionId": connection_id,
    }
    
    params["Signature"] = generate_signature(params)
    query_string = parse.urlencode(sorted(params.items()))
    url = f"wss://{HOST}/api/v1/flow_tts/bidirection?{query_string}"
    
    return url, connection_id


class TTSWebSocketClient:
    def __init__(self):
        self.ws = None
        self.connection_id = None
        self.session_id = None
        self.session = None
        self.audio_chunks = []  # 收到的音频分片，按到达顺序拼接

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
            audio = base64.b64decode(data.get("Audio", ""))
            if audio:
                self.audio_chunks.append(audio)
            print(f"收到句子[{data.get('SentenceId')}]: {data.get('Sentence')} "
                  f"(音频: {len(audio)} 字节, IsEnd={data.get('IsEnd')})")

        elif event == "SessionEnd":
            data = msg.get("Data", {})
            print(f"会话结束 - 句子数: {data.get('TotalSentences')}, 时长: {data.get('TotalDuration')}秒")
            self.save_audio()
            await self.ws.close()

        elif event == "SessionError":
            error_data = msg.get("Data", {})
            print(f"会话错误: {error_data.get('ErrorCode')} - {error_data.get('ErrorMessage')}")

        elif event == "SentenceError":
            error_data = msg.get("Data", {})
            print(f"句子错误: {error_data}")

    def save_audio(self):
        """把收到的音频分片拼接落盘"""
        if not self.audio_chunks:
            return
        data = b"".join(self.audio_chunks)
        if AUDIO_FORMAT == "pcm":
            data = pcm_to_wav(data, SAMPLE_RATE)
        ext = FILE_EXT.get(AUDIO_FORMAT, AUDIO_FORMAT)
        filename = f"ws_bidirection_{VOICE_ID}_{int(time.time())}.{ext}"
        with open(filename, "wb") as f:
            f.write(data)
        print(f"音频已保存: {filename} ({len(data)} 字节)")
        if AUDIO_FORMAT == "opus":
            # 每句是一条独立的 Ogg 流，直接拼接得到 chained Ogg：
            # ffmpeg / VLC 可正常播放，部分浏览器只会播第一段，需要时转码即可
            print(f"提示: 如需单流文件可执行 ffmpeg -i {filename} out.wav")

    async def start_session(self):
        """开始会话"""
        message = {
            "Event": "StartSession",
            "ConnectionId": self.connection_id,
            "SessionId": "",
            "MessageId": str(uuid.uuid4()),
            "Data": {
                "Language": "zh",
                "Model": MODEL,
                "AudioFormat": {
                    "Format": AUDIO_FORMAT,
                    "SampleRate": SAMPLE_RATE,
                    "BitRate": BIT_RATE,
                },
                "Voice": {
                    "VoiceId": VOICE_ID,
                    "Speed": 1.0,
                    "Volume": 1.0,
                    "Pitch": 0,
                },
            },
        }

        await self.ws.send_str(json.dumps(message, ensure_ascii=False))
        print(f"已发送StartSession (Model={MODEL}, VoiceId={VOICE_ID}, "
              f"Format={AUDIO_FORMAT}, SampleRate={SAMPLE_RATE})")

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