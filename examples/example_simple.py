#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlowTTS Simple Example - Streaming TTS with Keep-Alive
"""

import os
import io
import json
import wave
import base64
from dotenv import load_dotenv
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.trtc.v20190722 import trtc_client, models

# Load environment variables from .env file
load_dotenv()

# ========== Configuration ==========
# Environment variable takes priority, fallback to default
SDK_APP_ID = int(os.getenv("TENCENTCLOUD_SDK_APP_ID", "1400000000"))
MODEL = "flow_01_turbo"

VOICE_CONFIG = {
    "VoiceId": "v-female-R2s4N9qJ",  # Voice ID
    "Speed": 1.0,                    # Speed: [0.5, 2.0], default 1.0
    "Volume": 1.0,                   # Volume: [0, 10], default 1.0
    "Pitch": 0,                      # Pitch: [-12, 12], default 0
    "Language": "zh"                 # Language: zh/en/yue/ja/ko, default auto
}

AUDIO_FORMAT = {
    "Format": "pcm",      # Streaming SSE only supports pcm
    "SampleRate": 24000   # Sample rate: 16000 or 24000
}
# ===================================


def create_client():
    """
    Create Tencent Cloud TRTC client with Keep-Alive enabled.
    Keep-Alive reuses TCP connections for better performance.
    """
    cred = credential.Credential(
        os.getenv("TENCENTCLOUD_SECRET_ID"),
        os.getenv("TENCENTCLOUD_SECRET_KEY")
    )

    http_profile = HttpProfile()
    http_profile.endpoint = os.getenv(
        "TENCENTCLOUD_ENDPOINT",
        "trtc.ai.tencentcloudapi.com"
    )
    http_profile.reqTimeout = 120
    http_profile.keepAlive = True        # Enable Keep-Alive
    http_profile.pre_conn_pool_size = 3  # Connection pool size

    client_profile = ClientProfile()
    client_profile.httpProfile = http_profile

    return trtc_client.TrtcClient(cred, "ap-beijing", client_profile)


def pcm_to_wav(pcm_data, sample_rate=24000, channels=1, sample_width=2):
    """
    Convert PCM data to WAV format with proper header.

    Args:
        pcm_data: Raw PCM audio bytes
        sample_rate: Sample rate in Hz (default: 24000)
        channels: Number of channels (default: 1, mono)
        sample_width: Bytes per sample (default: 2, 16-bit)

    Returns:
        WAV format audio bytes
    """
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    return wav_buffer.getvalue()


def text_to_speech(client, text, output_file="output.wav"):
    """
    Convert text to speech using streaming SSE API.

    Args:
        client: TRTC client instance
        text: Text to synthesize
        output_file: Output audio file path (.wav)
    """
    req = models.TextToSpeechSSERequest()
    params = {
        "Model": MODEL,
        "Text": text,
        "Voice": VOICE_CONFIG,
        "AudioFormat": AUDIO_FORMAT,
        "SdkAppId": SDK_APP_ID  # From env or default
    }
    req.from_json_string(json.dumps(params))

    print(f"Synthesizing: {text}")

    # Streaming response
    resp = client.TextToSpeechSSE(req)

    audio_chunks = []
    for event in resp:
        if isinstance(event, dict) and 'data' in event:
            try:
                data = json.loads(event['data'].strip())
                if data.get('Type') == 'audio' and data.get('Audio'):
                    audio_chunks.append(base64.b64decode(data['Audio']))
                if data.get('IsEnd'):
                    break
            except (json.JSONDecodeError, KeyError):
                continue

    # Save audio to WAV file
    if audio_chunks:
        pcm_data = b''.join(audio_chunks)
        wav_data = pcm_to_wav(pcm_data, sample_rate=AUDIO_FORMAT["SampleRate"])

        with open(output_file, 'wb') as f:
            f.write(wav_data)

        print(f"Audio saved to: {output_file}")
        print(f"PCM size: {len(pcm_data)} bytes, WAV size: {len(wav_data)} bytes")
    else:
        print("No audio data received")


def main():
    # Create client (reuse for multiple requests)
    client = create_client()

    # Example: Single request with gentle female voice
    text_to_speech(
        client,
        "晚风轻轻吹过窗台，月光洒在你的脸上，愿今夜的星星都化作美梦，伴你安然入睡。晚安，亲爱的。",
        "output.wav"
    )


if __name__ == "__main__":
    main()
