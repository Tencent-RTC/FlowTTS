# FlowTTS Go Examples

These examples use the Tencent Cloud Go SDK for FlowTTS.

## Setup

Run from this directory:

```bash
go mod download
```

The examples load credentials from the project root `.env` file:

```env
TENCENTCLOUD_SECRET_ID=your_secret_id_here
TENCENTCLOUD_SECRET_KEY=your_secret_key_here
TENCENTCLOUD_SDK_APP_ID=1400000000
```

## Run

```bash
# Streaming SSE TTS, saves WAV
go run ./streaming

# Non-streaming TTS, saves MP3 and WAV
go run ./non_streaming

# Voice clone, prints VoiceId
go run ./voice_clone

# WebSocket bidirectional streaming (client streams text, server streams audio)
go run ./ws_bidirection

# Override model / voice via env
FLOW_TTS_MODEL=flow_01_ex FLOW_TTS_VOICE_ID=male-qn-qingse go run ./ws_bidirection
```

Generated audio files are saved in `examples/golang`.
