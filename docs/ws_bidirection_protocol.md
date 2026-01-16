# TTS WebSocket 协议文档

## 1. 概述

TTS WebSocket API 提供实时双向通信的文本转语音服务，支持客户端流式发送文本，服务端自动分句并实时返回音频数据。

### 核心特性

- **双向实时通信**：基于 WebSocket 协议的全双工通信
- **流式文本输入**：客户端可以持续发送文本片段，无需等待
- **自动分句**：服务端智能识别句子边界，按句合成音频
- **实时音频返回**：每个句子合成完成后立即返回音频
- **会话管理**：支持会话级别的音色参数配置

## 2. 连接建立（HTTP阶段）

WebSocket 连接建立前需要通过 HTTP GET 请求进行鉴权，参数包括：

**URL格式**：

注意：url中的query都需要进行urlencode

```
wss://flowtts.cloud.tencent.com/api/v1/flow_tts/bidirection?Action=TextToSpeechBidirection&AppId={appId}&SecretId={secretId}&SdkAppId={sdkAppId}&Timestamp={timestamp}&Expired={expired}&ConnectionId={connectionId}&Signature={signature}
```

### 2.1 鉴权参数详解

| 参数名 | 类型 | 必填 | 验证规则 | 说明 |
|--------|------|------|----------|------|
| Action | String | 是 | 固定值：`TextToSpeechBidirection` | 接口名称，必须为此固定值 |
| AppId | Integer | 是 | 非0整数 | 腾讯云AppId |
| SecretId | String | 是 | 非空字符串 | 云API密钥ID |
| SdkAppId | Integer | 是 | 非0整数 | TRTC应用ID |
| Timestamp | Integer | 是 | 非0整数 | 当前Unix时间戳（秒） |
| Expired | Integer | 是 | 非0整数，必须晚于Timestamp | 签名过期时间戳（秒） |
| ConnectionId | String | 是 | 非空字符串（建议UUID格式） | 客户端生成的连接ID，用于唯一标识连接 |
| Signature | String | 是 | 非空字符串，Base64编码 | 签名字符串（HMAC-SHA1算法，Base64编码） |

### 2.2 签名生成算法

详细内容可参考文档中的代码示例

1. 首先拼接签名原文，如下

```
SignString = HTTPMethod + URL路径 + "?" + 排序后的查询参数
```

示例：
```
GET/api/v1/flow_tts/bidirection?Action=TextToSpeechBidirection&AppId=1258344704&ConnectionId=abc123&Expired=1735834800&SecretId=AKIxjLx186ElarIZfdcMBpJbifS7awxbDrxB&SdkAppId=1400000001&Timestamp=1735748400
```

2. 对签名原文使用 SecretKey 进行 HMAC-SHA1 加密，之后再进行 base64 编码，得到Signature，注意Signature放入url时需要进行url encode


### 2.3 连接建立流程

```
客户端                                 服务端
---------------------------------------------------------------------
1. 生成 ConnectionId（建议 UUID）
2. 获取当前时间戳 Timestamp 和 Expired（过期时间）
3. 构造查询参数列表
4. 生成签名 Signature
5. 构造完整 WebSocket URL
6. 发送 WebSocket 连接请求（HTTP GET）
7. 服务端提取并验证参数
8. 调用 CAM 鉴权服务验证签名
9. 检查 TRTC 套餐包能力位
10. 返回 101 Switching Protocols（连接建立成功）
    或 HTTP 错误响应（鉴权失败或者参数错误 详细的错误内容在body里）
```

建连失败的http错误示例
```
{
  "Response": {
    "RequestId": "903bf8ec-4354-47d9-8864-3f45f1a81b2d",
    "Error": {
      "Code": "AuthFailure",
      "Message": "CAM authentication failed: [request id:6a3f65eb-03c8-4a7e-bdaa-2c9082b63c1d]secret id error"
    }
  }
}
```

### 2.4 连接限制

1.一条websocket连接最长保持5小时，超时会被强制关闭

2.websocket连接的读超时是10分钟，如果超过10分钟没收到信令数据，则会强制关闭websocket连接

3.一条websocket连接如果接收的文本字符数大于10000，会强制关闭websocket连接


## 3. 通用消息格式

所有 WebSocket 消息遵循统一格式：

```json
{
  "Event": "事件类型",
  "ConnectionId": "连接ID",
  "SessionId": "会话ID",
  "MessageId": "消息ID（UUID）",
  "Data": {
    // 事件相关数据
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| Event | String | 事件类型（见下文） |
| ConnectionId | String | 连接ID（由客户端在URL中提供） |
| SessionId | String | 会话ID（StartSession时由服务端生成） |
| MessageId | String | 消息唯一ID（UUID格式） |
| Data | Object | 事件相关的数据 |

## 4. 客户端信令（Client → Server）

### 4.1 StartSession - 开始会话

客户端发送此信令开始一个新的TTS会话，并指定音色参数。

**约束**：同一连接同时只能有一个活跃会话。

**消息格式**：
```json
{
  "Event": "StartSession",
  "ConnectionId": "550e8400-e29b-41d4-a716-446655440000",
  "SessionId": "",
  "MessageId": "msg-001",
  "Data": {
    "Language": "zh",
    "AudioFormat": {
      "Format": "pcm",
      "SampleRate": 16000,
      "BitRate": 128000
    },
    "Voice": {
      "VoiceId": "zh-CN-XiaoxiaoNeural",
      "Speed": 1.0,
      "Volume": 1.0,
      "Pitch": 1.0
    }
  }
}
```

**Data字段说明**：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| Language | String | 否 | zh-CN | 需要合成的语言（ISO 639-1），支持 zh（中文）、en（英文）、yue（粤语）、ja（日语）、ko（韩语），默认自动识别） |
| AudioFormat.Format | String | 否 | pcm | 音频格式（pcm/mp3）|
| AudioFormat.SampleRate | Integer | 否 | 24000 | 生成的音频采样率，默认24000，支持16000和24000  |
| AudioFormat.BitRate | Integer | 否 | 128 | MP3 比特率 (kbps)，仅对 MP3 格式生效, 可以选： 64, 128, 192, 256 , 默认： 128 |
| Voice.VoiceId | String | 是 | 无 | 音色 ID，可从音色列表获取，或使用声音克隆生成的自定义音色 ID |
| Voice.Speed | Float | 否 | 1.0 | 语速调节，0.5 为半速慢放，2.0 为两倍速快放，1.0 为正常语速，区间：[0.5, 2.0]，默认1.0 |
| Voice.Volume | Float | 否 | 1.0 | 音量调节，0 为静音，10 为最大音量，建议保持默认值 1.0，区间：[0, 10]，默认1.0 |
| Voice.Pitch | Float | 否 | 1.0 | 音高调节，负值声音更低沉，正值声音更尖锐，0 为原始音高，区间 [-12, 12], 默认0 |

### 3.2 ContinueSession - 流式发送文本

客户端持续发送文本片段，服务端缓存并自动分句。

**消息格式**：
```json
{
  "Event": "ContinueSession",
  "ConnectionId": "550e8400-e29b-41d4-a716-446655440000",
  "SessionId": "sess-7f8e9d0c",
  "MessageId": "msg-002",
  "Data": {
    "Text": "今天天气真好"
  }
}
```

**Data字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| Text | String | 是 | 文本片段，单次限制最大1000字符 |

### 3.3 FinishSession - 结束会话

客户端发送此信令表示文本输入结束，服务端将缓冲区剩余文本合成为最后一个句子。

**消息格式**：
```json
{
  "Event": "FinishSession",
  "ConnectionId": "550e8400-e29b-41d4-a716-446655440000",
  "SessionId": "sess-7f8e9d0c",
  "MessageId": "msg-003",
  "Data": {}
}
```

### 3.4 InterruptSession - 立即打断

客户端发送此信令立即停止当前会话的所有处理。

**消息格式**：
```json
{
  "Event": "InterruptSession",
  "ConnectionId": "550e8400-e29b-41d4-a716-446655440000",
  "SessionId": "sess-7f8e9d0c",
  "MessageId": "msg-004",
  "Data": {}
}
```

## 4. 服务端事件（Server → Client）

### 4.1 SessionStart - 会话开始

服务端响应`StartSession`信令，表示会话创建成功。

**消息格式**：
```json
{
  "Event": "SessionStart",
  "ConnectionId": "550e8400-e29b-41d4-a716-446655440000",
  "SessionId": "sess-7f8e9d0c",
  "MessageId": "msg-resp-001",
  "Data": {
    "Message": "Session started successfully",
    "VoiceParams": {
      "Language": "zh",
      "AudioFormat": {
        "Format": "pcm",
        "SampleRate": 24000
      },
      "Voice": {
        "VoiceId": "zh-CN-XiaoxiaoNeural",
        "Speed": 1.0,
        "Volume": 1.0,
        "Pitch": 1.0
      }
    }
  }
}
```

### 4.2 SessionEnd - 会话结束

会话正常结束（`FinishSession`）或被打断（`InterruptSession`）时发送。

**消息格式**：
```json
{
  "Event": "SessionEnd",
  "ConnectionId": "550e8400-e29b-41d4-a716-446655440000",
  "SessionId": "sess-7f8e9d0c",
  "MessageId": "msg-resp-005",
  "Data": {
    "TotalSentences": 8,
    "TotalDuration": 25.6,
    "Interrupted": false
  }
}
```

**Data字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| TotalSentences | Integer | 本次会话合成的句子总数 |
| TotalDuration | Float | 音频总时长（秒） |
| Interrupted | Boolean | 是否被客户端打断 |

### 4.3 SentenceAudio - 句子音频数据

每个句子合成完成后，服务端发送此事件返回音频数据。

**消息格式**：
```json
{
  "Event": "SentenceAudio",
  "ConnectionId": "550e8400-e29b-41d4-a716-446655440000",
  "SessionId": "sess-7f8e9d0c",
  "MessageId": "msg-audio-001",
  "Data": {
    "SentenceId": 1,
    "Sentence": "今天天气真好！",
    "Audio": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAgD4AAAB9AAACABAAZGF0YQAAAAA=",
    "Duration": 2.5,
    "IsEnd": false
  }
}
```

**Data字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| SentenceId | Integer | 句子序号（从1开始） |
| Sentence | String | 原始文本 |
| Audio | String | Base64编码的音频数据 |
| Duration | Float | 音频时长（秒） |
| IsEnd | Boolean | 该句的合成是否结束 |

### 4.4 SessionError - 会话级别错误

会话级别的错误（如参数无效、会话状态异常等）。

**消息格式**：
```json
{
  "Event": "SessionError",
  "ConnectionId": "550e8400-e29b-41d4-a716-446655440000",
  "SessionId": "sess-7f8e9d0c",
  "MessageId": "msg-error-001",
  "Data": {
    "ErrorCode": "InvalidParameter.VoiceId",
    "ErrorMessage": "Invalid VoiceId parameter"
  }
}
```

### 4.5 SentenceError - 句子级别错误

单个句子合成失败时发送，会话继续。

**消息格式**：
```json
{
  "Event": "SentenceError",
  "ConnectionId": "550e8400-e29b-41d4-a716-446655440000",
  "SessionId": "sess-7f8e9d0c",
  "MessageId": "msg-error-002",
  "Data": {
    "SentenceId": 3,
    "Sentence": "这是第三个句子。",
    "ErrorCode": "InternalError.TTSServiceUnavailable",
    "ErrorMessage": "TTS service temporarily unavailable"
  }
}
```

## 5. 错误码表

### 5.1 参数错误

| 错误码 | 说明 |
|--------|------|
| `InvalidParameter` | 无效参数 |
| `InvalidParameter.Action` | 无效Action参数 |
| `InvalidParameter.SecretId` | 无效SecretId |
| `InvalidParameter.ConnectionId` | 无效ConnectionId |
| `InvalidParameter.Signature` | 无效签名 |
| `InvalidParameter.AppId` | 无效AppId |
| `InvalidParameter.SdkAppId` | 无效SdkAppId |
| `InvalidParameter.Timestamp` | 无效时间戳 |
| `InvalidParameter.Expired` | 无效过期时间 |
| `InvalidParameter.TextLength` | 文本过长 |
| `InvalidParameter.Voice` | 无效音色参数 |

### 5.2 鉴权错误

| 错误码 | 说明 |
|--------|------|
| `AuthFailure` | 鉴权失败 |
| `AuthFailure.TimestampExpired` | 签名过期 |

### 5.3 内部错误

| 错误码 | 说明 |
|--------|------|
| `InternalError` | 内部错误 |
| `InternalError.TTSServiceUnavailable` | TTS服务不可用 |

### 5.4 配额错误

| 错误码 | 说明 |
|--------|------|
| `QuotaLimited` | 并发受限 |

### 5.5 消息错误

| 错误码 | 说明 |
|--------|------|
| `InvalidMessage` | 无效消息 |
| `InvalidMessage.StartSession` | 无效StartSession消息 |
| `InvalidMessage.ContinueSession` | 无效ContinueSession消息 |
| `InvalidMessage.FinishSession` | 无效FinishSession消息 |
| `InvalidMessage.InterruptSession` | 无效InterruptSession消息 |


## 6.示例
```python
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
```


## 常见问题

### Q：为什么鉴权失败？

A：检查以下几点：
1. SECRET_ID 和 SECRET_KEY 是否正确
2. Timestamp 是否为当前时间
3. 签名算法是否正确（HMAC-SHA1，Base64编码）
4. URL参数是否按字母序排序

如果websocket建连失败，且您使用的代码库不方便拿到http body里面的内容，可以把您的url使用如下代码进行测试
注意：服务返回的错误信息都是json格式，如果是其他错误，正常情况下websocket是可以建连成功的
```python
import aiohttp
import asyncio

async def request_flow_tts_ws(url):
    http_url = url.replace("wss://", "http://")
    print(f"尝试使用HTTP请求获取完整响应...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(http_url) as response:
            print(f"HTTP状态码: {response.status}")
            print(f"HTTP响应头: {dict(response.headers)}")
            print(f"HTTP响应body: {await response.text()}")

if __name__ == "__main__":
    url = "your-url"
    asyncio.run(request_flow_tts_ws(url))
```

### Q：为什么没有收到 SentenceAudio？

A：可能原因：
1. 文本未包含句子结束标点
2. 需要发送 FinishSession 触发最后一个句子
3. TTS 服务临时故障（检查 SentenceError 事件）

### Q：如何提高并发限制？

A：联系技术团队，根据业务需求申请配额提升。