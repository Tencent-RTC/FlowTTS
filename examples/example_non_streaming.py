#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlowTTS Non-Streaming Example - TextToSpeech with MP3/PCM support

This example demonstrates the non-streaming TTS API which returns
the complete audio in a single response. Supports MP3 and PCM formats.

API Reference:
- https://cloud.tencent.com/document/api/647/122475
- https://cloud.tencent.com/document/api/647/44055#AudioFormat
"""

import os
import io
import json
import time
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
SDK_APP_ID = int(os.getenv("TENCENTCLOUD_SDK_APP_ID", "1400000000"))
MODEL = "flow_01_turbo"

VOICE_CONFIG = {
    "VoiceId": "v-female-R2s4N9qJ",
    "Speed": 1.0,
    "Volume": 1.0,
    "Pitch": 0,
    "Language": "zh"
}

# Audio format configuration
# For non-streaming API, both "mp3" and "pcm" are supported
AUDIO_FORMAT = {
    "Format": "mp3",       # "mp3" or "pcm"
    "SampleRate": 24000    # 16000 or 24000
}

TEST_TEXT = "欢迎使用腾讯云语音合成服务，祝您使用愉快！"
# ===================================


def create_client():
    """Create Tencent Cloud TRTC client."""
    secret_id = os.getenv("TENCENTCLOUD_SECRET_ID")
    secret_key = os.getenv("TENCENTCLOUD_SECRET_KEY")
    
    if not secret_id or not secret_key:
        print("Error: TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY are required")
        return None
    
    cred = credential.Credential(secret_id, secret_key)
    
    http_profile = HttpProfile()
    http_profile.endpoint = os.getenv(
        "TENCENTCLOUD_ENDPOINT",
        "trtc.ai.tencentcloudapi.com"
    )
    http_profile.reqTimeout = 120
    http_profile.keepAlive = True
    http_profile.pre_conn_pool_size = 3
    
    client_profile = ClientProfile()
    client_profile.httpProfile = http_profile
    
    return trtc_client.TrtcClient(cred, "ap-beijing", client_profile)


def pcm_to_wav(pcm_data, sample_rate=24000, channels=1, sample_width=2):
    """Convert PCM data to WAV format."""
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    return wav_buffer.getvalue()


def save_audio_file(audio_data, filename):
    """Save audio data to file."""
    output_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'wb') as f:
        f.write(audio_data)
    
    print(f"   Audio saved to: {filepath}")
    return filepath


def text_to_speech_non_streaming(text=None, audio_format="mp3"):
    """
    Non-streaming TTS API.
    
    Args:
        text: Text to synthesize (default: TEST_TEXT)
        audio_format: Output format, "mp3" or "pcm" (default: "mp3")
    
    Returns:
        Path to the saved audio file, or None on failure
    """
    if text is None:
        text = TEST_TEXT
    
    print(f"\nStarting TTS synthesis")
    print(f"   Voice: {VOICE_CONFIG['VoiceId']}")
    print(f"   Text: {text}")
    print(f"   Text length: {len(text)}")
    print(f"   Format: {audio_format}")
    
    try:
        client = create_client()
        if not client:
            return None
        
        req = models.TextToSpeechRequest()
        
        # Configure audio format
        audio_config = {
            "Format": audio_format,
            "SampleRate": AUDIO_FORMAT["SampleRate"]
        }
        
        params = {
            "Model": MODEL,
            "Text": text,
            "Voice": VOICE_CONFIG,
            "AudioFormat": audio_config,
            "SdkAppId": SDK_APP_ID
        }
        req.from_json_string(json.dumps(params))
        
        print(f"   SdkAppId: {SDK_APP_ID}")
        
        start_time = time.time()
        resp = client.TextToSpeech(req)
        end_time = time.time()
        
        if hasattr(resp, 'Audio') and resp.Audio:
            audio_b64 = resp.Audio
            audio_data = base64.b64decode(audio_b64)
            
            # Print RequestId
            request_id = getattr(resp, 'RequestId', 'N/A')
            print(f"   RequestId: {request_id}")
            
            # Handle audio based on format
            if audio_format == "mp3":
                # MP3 format - save directly
                print(f"   MP3 data size: {len(audio_data)} bytes")
                print(f"   Time elapsed: {(end_time - start_time) * 1000:.0f}ms")
                filename = f"tts_{VOICE_CONFIG['VoiceId']}_{int(time.time())}.mp3"
                result = save_audio_file(audio_data, filename)
            else:
                # PCM format - convert to WAV
                wav_data = pcm_to_wav(audio_data, sample_rate=AUDIO_FORMAT["SampleRate"])
                print(f"   WAV data size: {len(wav_data)} bytes")
                print(f"   Time elapsed: {(end_time - start_time) * 1000:.0f}ms")
                filename = f"tts_{VOICE_CONFIG['VoiceId']}_{int(time.time())}.wav"
                result = save_audio_file(wav_data, filename)
            
            if result:
                print(f"\nTTS synthesis successful!")
                return result
        else:
            print("Error: No audio data in response")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    """Run examples for both MP3 and PCM formats."""
    # Example 1: MP3 format (default)
    print("=" * 50)
    print("Example 1: MP3 Format")
    print("=" * 50)
    text_to_speech_non_streaming(
        "欢迎使用腾讯云FlowTTS，这是MP3格式输出。",
        audio_format="mp3"
    )
    
    # Example 2: PCM format (converted to WAV)
    print("\n" + "=" * 50)
    print("Example 2: PCM Format (saved as WAV)")
    print("=" * 50)
    text_to_speech_non_streaming(
        "欢迎使用腾讯云FlowTTS，这是PCM格式输出。",
        audio_format="pcm"
    )


if __name__ == "__main__":
    main()
