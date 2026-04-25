<div align="center">

# FlowTTS

**新一代低延迟对话式语音合成系统**

[![GitHub](https://img.shields.io/badge/GitHub-Tencent--RTC%2FFlowTTS-181717?logo=github)](https://github.com/Tencent-RTC/FlowTTS)
[![TRTC](https://img.shields.io/badge/TRTC-AI-blue.svg)](https://cloud.tencent.com/product/trtc)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Tencent-RTC/FlowTTS/blob/main/LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Tencent-RTC/FlowTTS/pulls)

[English](https://github.com/Tencent-RTC/FlowTTS/blob/main/README_EN.md) | 简体中文

仓库地址：<https://github.com/Tencent-RTC/FlowTTS>

</div>

---

FlowTTS: 一个低延迟、可声音克隆、具备拟人化表达能力的新一代语音生成系统。它能够自然呈现语气词、情绪与副语言细节，让对话场景中的 AI"听起来像真人"。

> 🎧 **在线体验**：[对话式 TTS 全部音色体验页](https://web.realtime-ai.chat/app/tts.html)　·　📚 **协议细节**：[WebSocket 双向流式协议](https://github.com/Tencent-RTC/FlowTTS/blob/main/docs/ws_bidirection_protocol.md)

## 目录

- [特性](#特性)
- [模型说明](#模型说明)
- [快速开始](#快速开始)
- [示例索引](#示例索引)
- [如何选择接口](#如何选择接口)
- [API 参考](#api-参考)
- [Keep-Alive 长连接](#keep-alive-长连接)
- [API 文档](#api-文档)
- [TRTC AI 对话集成](#trtc-ai-对话集成)

## 特性

- **超低延迟**：流式 SSE API，支持 Keep-Alive 长连接
- **声音克隆**：提交少量语音样本，创建专属克隆音色
- **拟人化表达**：自然呈现语气词、情绪与副语言细节
- **多语言支持**：覆盖中、英、日、韩、粤、马来、阿拉伯、印尼、泰、越南共 10 种语言（详见 [语言代码](#语言代码iso-639-1)）

## 模型说明

| 模型 | 定位 | 特点 |
|------|------|------|
| `flow_02_turbo` | 对话场景（最新） | 超低延迟、音质高、拟人度强 |
| `flow_01_turbo` | 对话场景 | 超低延迟、音质高、拟人度强 |

两个模型均支持上述 10 种语言。

> 💡 **推荐**：`Model` 字段传空字符串 `""` 即可自动使用最新模型，无需手动指定版本。

## 快速开始

### 1. 开通服务

FlowTTS 依托 TRTC AI 对话方案使用，需先开通以下任一服务：

- AI 智能识别包（轻量版/尊享版）
- TRTC 包月套餐 Plus 能力

详见 [TRTC 开通 & 计费说明](https://cloud.tencent.com/document/product/647/111976)

### 2. 安装依赖

**Python**

```bash
cd examples/python
pip install -r requirements.txt
```

> 注意：请确保安装最新版本的腾讯云 SDK（>=3.0.1200），以获得完整的 TTS 功能支持。

**Node.js**

```bash
cd examples/nodejs
npm install
```

> 需要 Node.js >= 18。

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入腾讯云密钥：

```env
TENCENTCLOUD_SECRET_ID=your_secret_id_here
TENCENTCLOUD_SECRET_KEY=your_secret_key_here
TENCENTCLOUD_SDK_APP_ID=1400000000

# 可选：自定义 API Endpoint（默认 trtc.ai.tencentcloudapi.com）
TENCENTCLOUD_ENDPOINT=trtc.ai.tencentcloudapi.com
```

获取密钥：[腾讯云控制台](https://console.cloud.tencent.com/cam/capi)

### 4. 运行示例

从仓库根目录执行（任选一种语言）：

```bash
# Python
python examples/python/example_streaming.py

# Node.js
node examples/nodejs/example_streaming.js
```

> 第一次跑建议从 `example_streaming` 开始，能在数百毫秒内听到首个音频包。

#### 声音克隆流程

```bash
# 1. 准备音频样本（16kHz 单声道 WAV，10-180 秒）
cp your_voice.wav test_data/clone_sample.wav

# 2. 克隆声音，获取 voice_id
python examples/python/example_voice_clone.py

# 3. 在 example_streaming.py 中将 VOICE_CONFIG["VoiceId"] 改为返回的 voice_id 后运行
python examples/python/example_streaming.py
```

## 示例索引

仓库提供 4 套示例，Python 与 Node.js 一一对应。从根目录执行（Node.js 需先 `cd examples/nodejs`）：

| 场景 | Python | Node.js | 说明 |
|------|--------|---------|------|
| 流式合成（推荐入门） | `example_streaming.py` | `example_streaming.js` | SSE 流式返回，边合成边播放，首包延迟最低 |
| 非流式合成 | `example_non_streaming.py` | `example_non_streaming.js` | 一次性返回完整音频，适合离线/异步生成 |
| 声音克隆 | `example_voice_clone.py` | `example_voice_clone.js` | 上传音频样本，得到自定义 `VoiceId` |
| WebSocket 双向流式 | `example_ws_bidirection.py` | `example_ws_bidirection.js` | 边发文本边收音频，适合 LLM 流式输出对接 |

## 如何选择接口

| 场景 | 推荐接口 | 原因 |
|------|----------|------|
| 实时对话、Agent 语音输出 | **WebSocket 双向流式** | LLM token 流式产出后即时推给 TTS，首句最快出声，可中途打断 |
| 已知完整文本，要求最低首包延迟 | **流式 SSE** | 一次请求边收边播，比非流式延迟低 50-100ms |
| 离线播报、批量生成、文件导出 | **非流式** | 拿到完整音频文件（pcm/wav/mp3），方便后处理 |
| 需要专属音色 | **声音克隆** | 提交样本得到 `VoiceId`，再配合上述任意接口使用 |

## API 参考

### 语音参数

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| Speed | 0.5 ~ 2.0 | 1.0 | 语速，0.5 为半速、2.0 为两倍速 |
| Volume | (0, 10] | 1.0 | 音量，必须大于 0 |
| Pitch | -12 ~ 12 | 0 | 音高，负值更低沉、正值更尖锐 |

### 音频格式

| 接口类型 | 支持格式 | 采样率 |
|----------|----------|--------|
| 流式 (SSE) | pcm | 16000, 24000 |
| 非流式 | pcm, wav, mp3 | 16000, 24000 |

> 默认格式：pcm，默认采样率：24000

### API Endpoint

不同接口使用不同的 endpoint，请注意区分：

| 接口 | Endpoint |
|------|----------|
| 流式 SSE (`TextToSpeechSSE`) | `trtc.ai.tencentcloudapi.com` |
| 非流式 (`TextToSpeech`) | `trtc.tencentcloudapi.com` |
| 声音克隆 (`VoiceClone`) | `trtc.tencentcloudapi.com` |

## Keep-Alive 长连接

SDK 支持 HTTP Keep-Alive，复用 TCP 连接以降低延迟：

**Python**

```python
http_profile = HttpProfile()
http_profile.keepAlive = True        # 启用 Keep-Alive
http_profile.pre_conn_pool_size = 3  # 连接池大小
```

| 参数 | 说明 |
|------|------|
| `keepAlive` | 启用后复用 TCP 连接，避免重复握手，降低后续请求延迟 |
| `pre_conn_pool_size` | 预建连接池大小，提前建立连接，首次请求也能快速响应 |

> 启用 Keep-Alive 后，连续请求可节省约 50-100ms 的连接建立时间

**Node.js**

Node.js HTTP agent 默认支持连接复用，无需额外配置。

## API 文档

**官方 API**

- [SSE 流式文本转语音 API](https://cloud.tencent.com/document/product/647/122474)
- [非流式文本转语音 API](https://cloud.tencent.com/document/api/647/122475)
- [声音克隆 API](https://cloud.tencent.com/document/product/647/122473)

**仓库内文档**

- [WebSocket 双向流式协议](https://github.com/Tencent-RTC/FlowTTS/blob/main/docs/ws_bidirection_protocol.md) — 鉴权、消息格式、事件、错误码、完整示例
- [字符计算规则](https://github.com/Tencent-RTC/FlowTTS/blob/main/docs/char_count_rules.md) — 计费与文本长度限制使用的字符计数规则

**音色与体验**

- [精品音色列表](https://doc.weixin.qq.com/smartsheet/s3_AS8AdAZRAHECNorj3TwZ8REagnFMY?scode=AJEAIQdfAAolPNM7ckAS8AdAZRAHE&tab=q979lj&viewId=vukaF8)
- [对话式 TTS 全部音色体验页](https://web.realtime-ai.chat/app/tts.html)

## TRTC AI 对话集成

在 TRTC AI 对话配置中加入 TTS 配置，`TTSConfig`：

- [对话式 AI TTS 配置](https://cloud.tencent.com/document/product/647/115414)

```json
{
  "TTSType": "flow",
  "VoiceId": "your_voice_id",
  "Model": "",
  "Speed": 1.0,
  "Volume": 1.0,
  "Pitch": 0,
  "Language": "zh"
}
```

### 语言代码（ISO 639-1）

| 语言 | 代码 |
|------|------|
| 中文 | zh |
| 英文 | en |
| 日语 | ja |
| 韩语 | ko |
| 粤语 | yue |
| 马来语 | ms |
| 阿拉伯语 | ar |
| 印尼语 | id |
| 泰语 | th |
| 越南语 | vi |

## License

MIT License - see [LICENSE](https://github.com/Tencent-RTC/FlowTTS/blob/main/LICENSE) for details.
