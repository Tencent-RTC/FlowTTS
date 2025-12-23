<div align="center">

# FlowTTS

**新一代低延迟对话式语音合成系统**

[![TRTC](https://img.shields.io/badge/TRTC-AI-blue.svg)](https://cloud.tencent.com/product/trtc)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Tencent-RTC/FlowTTS/pulls)

[English](README_EN.md) | 简体中文

</div>

---

FlowTTS: 一个低延迟、可声音克隆、具备拟人化表达能力的新一代语音生成系统。它能够自然呈现语气词、情绪与副语言细节，让对话场景中的 AI "听起来像真人"。

## 在线体验

- [对话式 TTS 全部音色体验页](https://web.realtime-ai.chat/app/tts.html)

## 特性

- **超低延迟**: 流式 SSE API，支持 Keep-Alive 长连接
- **声音克隆**: 提交少量语音样本，创建专属克隆音色
- **拟人化表达**: 自然呈现语气词、情绪与副语言细节
- **多语言支持**: 中/英/日/韩/粤语

## 模型说明

| 模型 | 定位 | 特点 |
|------|------|------|
| `flow_01_turbo` | 对话场景主推 | 超低延迟，音质高，拟人度强，支持中/英/日/韩/粤语 |

### 音色列表

- [flow_01_turbo 精品音色列表](https://doc.weixin.qq.com/smartsheet/s3_AS8AdAZRAHECNorj3TwZ8REagnFMY?scode=AJEAIQdfAAolPNM7ckAS8AdAZRAHE&tab=q979lj&viewId=vukaF8)

## 快速开始

### 1. 开通服务

FlowTTS 依托 TRTC AI 对话方案使用，需先开通以下任一服务：

- AI 智能识别包（轻量版/尊享版）
- TRTC 包月套餐 Plus 能力

详见 [TRTC 开通 & 计费说明](https://cloud.tencent.com/document/product/647/111976)

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

> 注意：请确保安装最新版本的腾讯云 SDK（>=3.0.1200），以获得完整的 TTS 功能支持。

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入腾讯云密钥：

```env
TENCENTCLOUD_SECRET_ID=your_secret_id_here
TENCENTCLOUD_SECRET_KEY=your_secret_key_here
TENCENTCLOUD_SDK_APP_ID=1400000000
```

获取密钥：[腾讯云控制台](https://console.cloud.tencent.com/cam/capi)

### 4. 运行示例

#### 基础 TTS 示例

```bash
python examples/example_simple.py
```

#### 声音克隆示例

```bash
# 1. 准备音频样本（16kHz 单声道 WAV，10-180秒）
cp your_voice.wav test_data/clone_sample.wav

# 2. 克隆声音，获取 voice_id
python examples/example_voice_clone.py

# 3. 在 example_simple.py 中使用返回的 voice_id 进行 TTS 合成
# 修改 VOICE_CONFIG["VoiceId"] 为克隆返回的 voice_id
python examples/example_simple.py
```

## 参数配置

### 语音参数

| 参数 | 范围 | 说明 |
|------|------|------|
| Speed | 0.5 ~ 2.0 | 语速 |
| Volume | 0 ~ 10 | 音量 |
| Pitch | -12 ~ 12 | 音高 |

### 音频格式

| 接口类型 | 支持格式 | 采样率 |
|----------|----------|--------|
| 流式 (SSE) | pcm | 16000, 24000 |
| 非流式 | pcm, wav | 16000, 24000 |

> 默认格式：pcm，默认采样率：24000

## Keep-Alive 长连接

SDK 支持 HTTP Keep-Alive，复用 TCP 连接以降低延迟：

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

## API 文档

- [SSE 流式文本转语音 API](https://cloud.tencent.com/document/product/647/122474)
- [声音克隆 API](https://cloud.tencent.com/document/product/647/122473)

## TRTC AI 对话集成

在 TRTC AI 对话配置中加入 TTS 配置，`TTSConfig`：

- [对话式 AI TTS 配置](https://cloud.tencent.com/document/product/647/115414)

```json
{
  "TTSType": "flow",
  "VoiceId": "your_voice_id",
  "Model": "flow_01_turbo",
  "Speed": 1.0,
  "Volume": 1.0,
  "Pitch": 0,
  "Language": "zh"
}
```

## License

MIT License - see [LICENSE](LICENSE) for details.
