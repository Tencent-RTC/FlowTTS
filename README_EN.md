<div align="center">

# FlowTTS

**Next-Generation Low-Latency Conversational Speech Synthesis**

[![TRTC](https://img.shields.io/badge/TRTC-AI-blue.svg)](https://cloud.tencent.com/product/trtc)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Tencent-RTC/FlowTTS/pulls)

English | [简体中文](README.md)

</div>

---

FlowTTS: A next-generation low-latency speech synthesis system with voice cloning and human-like expression capabilities. It naturally presents filler words, emotions, and paralinguistic details, making AI in dialogue scenarios "sound like a real person".

## Online Demo

- [FlowTTS Voice Experience Page](https://web.realtime-ai.chat/app/tts.html)

## Features

- **Ultra-Low Latency**: Streaming SSE API with Keep-Alive connection
- **Voice Cloning**: Create custom voice by submitting audio samples
- **Human-like Expression**: Natural filler words, emotions, and paralinguistic details
- **Multi-language Support**: Chinese/English/Japanese/Korean/Cantonese

## Models

| Model | Use Case | Features |
|-------|----------|----------|
| `flow_01_turbo` | Conversational (Recommended) | Ultra-low latency, high quality, supports Chinese/English/Japanese/Korean/Cantonese |

### Voice List

- [flow_01_turbo Premium Voice List](https://doc.weixin.qq.com/smartsheet/s3_AS8AdAZRAHECNorj3TwZ8REagnFMY?scode=AJEAIQdfAAolPNM7ckAS8AdAZRAHE&tab=q979lj&viewId=vukaF8)

## Quick Start

### 1. Enable Service

FlowTTS is built on TRTC AI Conversation solution. You need to enable one of the following:

- AI Recognition Package (Lite/Premium)
- TRTC Monthly Plus Plan

See [TRTC Activation & Billing](https://cloud.tencent.com/document/product/647/111976)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

> Note: Please ensure you install the latest version of Tencent Cloud SDK (>=3.0.1200) for full TTS feature support.

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your Tencent Cloud credentials:

```env
TENCENTCLOUD_SECRET_ID=your_secret_id_here
TENCENTCLOUD_SECRET_KEY=your_secret_key_here
TENCENTCLOUD_SDK_APP_ID=1400000000
```

Get credentials from [Tencent Cloud Console](https://console.cloud.tencent.com/cam/capi)

### 4. Run Examples

#### Basic TTS Example

```bash
python examples/example_simple.py
```

#### Voice Clone Example

```bash
# 1. Prepare audio sample (16kHz mono WAV, 10-180 seconds)
cp your_voice.wav test_data/clone_sample.wav

# 2. Clone voice and get voice_id
python examples/example_voice_clone.py

# 3. Use the returned voice_id in example_simple.py for TTS
# Update VOICE_CONFIG["VoiceId"] with the cloned voice_id
python examples/example_simple.py
```

## Configuration

### Voice Parameters

| Parameter | Range | Description |
|-----------|-------|-------------|
| Speed | 0.5 ~ 2.0 | Speech speed |
| Volume | 0 ~ 10 | Volume level |
| Pitch | -12 ~ 12 | Pitch adjustment |

### Audio Format

| API Type | Formats | Sample Rates |
|----------|---------|--------------|
| Streaming (SSE) | pcm | 16000, 24000 |
| Non-streaming | pcm, wav | 16000, 24000 |

> Default format: pcm, default sample rate: 24000

## Keep-Alive Connection

The SDK supports HTTP Keep-Alive to reuse TCP connections and reduce latency:

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

## API Documentation

- [SSE Streaming Text-to-Speech API](https://cloud.tencent.com/document/product/647/122474)
- [Voice Cloning API](https://cloud.tencent.com/document/product/647/122473)

## TRTC AI Conversation Integration

Add TTS configuration in TRTC AI Conversation settings, `TTSConfig`:

- [AI Conversation TTS Configuration](https://cloud.tencent.com/document/product/647/115414)

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

### Language Codes (ISO 639-1)

| Language | Code |
|----------|------|
| Chinese | zh |
| English | en |
| Japanese | ja |
| Korean | ko |
| Cantonese | yue |

## License

MIT License - see [LICENSE](LICENSE) for details.
