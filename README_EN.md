<div align="center">

# FlowTTS

**Next-Generation Low-Latency Conversational Speech Synthesis**

[![GitHub](https://img.shields.io/badge/GitHub-Tencent--RTC%2FFlowTTS-181717?logo=github)](https://github.com/Tencent-RTC/FlowTTS)
[![TRTC](https://img.shields.io/badge/TRTC-AI-blue.svg)](https://cloud.tencent.com/product/trtc)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Tencent-RTC/FlowTTS/blob/main/LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Tencent-RTC/FlowTTS/pulls)

English | [简体中文](https://github.com/Tencent-RTC/FlowTTS/blob/main/README.md)

Repository: <https://github.com/Tencent-RTC/FlowTTS>

</div>

---

FlowTTS: A next-generation low-latency speech synthesis system with voice cloning and human-like expression capabilities. It naturally presents filler words, emotions, and paralinguistic details, making AI in dialogue scenarios "sound like a real person".

## Online Demo

- [FlowTTS Voice Experience Page](https://web.realtime-ai.chat/app/tts.html)

## Features

- **Ultra-Low Latency**: Streaming SSE API with Keep-Alive connection
- **Voice Cloning**: Create custom voice by submitting audio samples
- **Human-like Expression**: Natural filler words, emotions, and paralinguistic details
- **Multi-language Support**: Chinese/English/Japanese/Korean/Cantonese/Malay/Arabic/Indonesian/Thai/Vietnamese

## Models

| Model | Use Case | Features |
|-------|----------|----------|
| `flow_02_turbo` | Conversational (Latest) | Ultra-low latency, high quality, supports Chinese/English/Japanese/Korean/Cantonese/Malay/Arabic/Indonesian/Thai/Vietnamese |
| `flow_01_turbo` | Conversational | Ultra-low latency, high quality, supports Chinese/English/Japanese/Korean/Cantonese/Malay/Arabic/Indonesian/Thai/Vietnamese |

> **Recommended:** Pass an empty string `""` for the `Model` field to automatically use the latest model without specifying a version.

### Voice List

- [Premium Voice List](https://doc.weixin.qq.com/smartsheet/s3_AS8AdAZRAHECNorj3TwZ8REagnFMY?scode=AJEAIQdfAAolPNM7ckAS8AdAZRAHE&tab=q979lj&viewId=vukaF8)

## Quick Start

### 1. Enable Service

FlowTTS is built on TRTC AI Conversation solution. You need to enable one of the following:

- AI Recognition Package (Lite/Premium)
- TRTC Monthly Plus Plan

See [TRTC Activation & Billing](https://cloud.tencent.com/document/product/647/111976)

### 2. Install Dependencies

**Python**

```bash
cd examples/python
pip install -r requirements.txt
```

> Note: Please ensure you install the latest version of Tencent Cloud SDK (>=3.0.1200) for full TTS feature support.

**Node.js**

```bash
cd examples/nodejs
npm install
```

> Requires Node.js >= 18.

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your Tencent Cloud credentials:

```env
TENCENTCLOUD_SECRET_ID=your_secret_id_here
TENCENTCLOUD_SECRET_KEY=your_secret_key_here
TENCENTCLOUD_SDK_APP_ID=1400000000

# Optional: custom API endpoint (defaults to trtc.ai.tencentcloudapi.com)
TENCENTCLOUD_ENDPOINT=trtc.ai.tencentcloudapi.com
```

Get credentials from [Tencent Cloud Console](https://console.cloud.tencent.com/cam/capi)

### 4. Run Examples

#### Python

```bash
# Streaming TTS
python examples/python/example_streaming.py

# Non-streaming TTS
python examples/python/example_non_streaming.py

# Voice cloning
python examples/python/example_voice_clone.py

# WebSocket bidirectional streaming
python examples/python/example_ws_bidirection.py
```

#### Node.js

```bash
cd examples/nodejs

# Streaming TTS
node example_streaming.js

# Non-streaming TTS
node example_non_streaming.js

# Voice cloning
node example_voice_clone.js

# WebSocket bidirectional streaming
node example_ws_bidirection.js
```

#### Voice Clone Example

```bash
# 1. Prepare audio sample (16kHz mono WAV, 10-180 seconds)
cp your_voice.wav test_data/clone_sample.wav

# 2. Clone voice and get voice_id
python examples/python/example_voice_clone.py

# 3. Use the returned voice_id in example_streaming.py for TTS
# Update VOICE_CONFIG["VoiceId"] with the cloned voice_id
python examples/python/example_streaming.py
```

## Configuration

### Voice Parameters

| Parameter | Range | Description |
|-----------|-------|-------------|
| Speed | 0.5 ~ 2.0 | Speech speed |
| Volume | 0.01 ~ 10 | Volume level (must be > 0) |
| Pitch | -12 ~ 12 | Pitch adjustment |

### Audio Format

| API Type | Formats | Sample Rates |
|----------|---------|--------------|
| Streaming (SSE) | pcm | 16000, 24000 |
| Non-streaming | pcm, wav, mp3 | 16000, 24000 |

> Default format: pcm, default sample rate: 24000

### API Endpoint

Different APIs use different endpoints:

| API | Endpoint |
|-----|----------|
| Streaming SSE (`TextToSpeechSSE`) | `trtc.ai.tencentcloudapi.com` |
| Non-streaming (`TextToSpeech`) | `trtc.tencentcloudapi.com` |
| Voice Clone (`VoiceClone`) | `trtc.tencentcloudapi.com` |

## Keep-Alive Connection

The SDK supports HTTP Keep-Alive to reuse TCP connections and reduce latency:

**Python**

```python
http_profile = HttpProfile()
http_profile.keepAlive = True        # Enable Keep-Alive
http_profile.pre_conn_pool_size = 3  # Connection pool size
```

| Parameter | Description |
|-----------|-------------|
| `keepAlive` | Reuses TCP connections, avoids repeated handshakes, reduces latency for subsequent requests |
| `pre_conn_pool_size` | Pre-established connection pool size, connections are ready before first request |

> With Keep-Alive enabled, consecutive requests save approximately 50-100ms of connection establishment time

**Node.js**

Node.js HTTP agent supports connection reuse by default, no additional configuration needed.

## API Documentation

- [SSE Streaming Text-to-Speech API](https://cloud.tencent.com/document/product/647/122474)
- [Non-streaming Text-to-Speech API](https://cloud.tencent.com/document/api/647/122475)
- [Voice Cloning API](https://cloud.tencent.com/document/product/647/122473)

### In-repo Docs

- [WebSocket Bidirectional Streaming Protocol](https://github.com/Tencent-RTC/FlowTTS/blob/main/docs/ws_bidirection_protocol.md) — auth, message format, events, error codes, full example
- [Character Counting Rules](https://github.com/Tencent-RTC/FlowTTS/blob/main/docs/char_count_rules.md) — character counting rules used for billing and text-length limits

## TRTC AI Conversation Integration

Add TTS configuration in TRTC AI Conversation settings, `TTSConfig`:

- [AI Conversation TTS Configuration](https://cloud.tencent.com/document/product/647/115414)

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

### Language Codes (ISO 639-1)

| Language | Code |
|----------|------|
| Chinese | zh |
| English | en |
| Japanese | ja |
| Korean | ko |
| Cantonese | yue |
| Malay | ms |
| Arabic | ar |
| Indonesian | id |
| Thai | th |
| Vietnamese | vi |

## License

MIT License - see [LICENSE](https://github.com/Tencent-RTC/FlowTTS/blob/main/LICENSE) for details.
