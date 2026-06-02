#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlowTTS flow_01_ex Example - Voice Clone + Inference

This example demonstrates the complete flow for the flow_01_ex model:
1. Clone a voice from a reference audio sample.
2. Use the returned VoiceId for non-streaming TTS inference.

Voice Clone and non-streaming TTS both use endpoint "trtc.tencentcloudapi.com".
"""

import os
import json
import time
import base64
from dotenv import load_dotenv
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.trtc.v20190722 import trtc_client, models
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException

# Load environment variables from .env file
load_dotenv()

# ========== Configuration ==========
SDK_APP_ID = int(os.getenv("TENCENTCLOUD_SDK_APP_ID") or os.getenv("SDKAPPID") or "1400000000")
MODEL = "flow_01_ex"

# Voice clone settings
CLONE_AUDIO_FILE = os.path.join(os.path.dirname(__file__), "../../test_data/clone_sample.wav")  # 16kHz mono WAV, 10-180 seconds
VOICE_NAME = "Flow01ExClonedVoice"
# (Optional) Transcript of the reference audio, improves clone quality
PROMPT_TEXT = ""
# (Optional) Language of the reference audio (ISO 639-1): zh/en/yue/ja/ko/ar/id/th, default auto
CLONE_LANGUAGE = ""

# TTS inference settings
INFERENCE_TEXT = "欢迎使用腾讯云 FlowTTS flow_01_ex 模型，这是克隆音色完成后的推理示例。"
INFERENCE_LANGUAGE = "zh"

VOICE_PARAMS = {
    "Speed": 1.0,
    "Volume": 1.0,
    "Pitch": 0,
}

AUDIO_FORMAT = {
    "Format": "mp3",
    "SampleRate": 24000,
}
# ===================================


def create_client():
    """Create Tencent Cloud TRTC client for VoiceClone and TextToSpeech."""
    secret_id = os.getenv("TENCENTCLOUD_SECRET_ID")
    secret_key = os.getenv("TENCENTCLOUD_SECRET_KEY")

    if not secret_id or not secret_key:
        print("Error: TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY are required")
        return None

    cred = credential.Credential(secret_id, secret_key)

    http_profile = HttpProfile()
    http_profile.endpoint = "trtc.tencentcloudapi.com"
    http_profile.reqTimeout = 120
    http_profile.keepAlive = True
    http_profile.pre_conn_pool_size = 3

    client_profile = ClientProfile()
    client_profile.httpProfile = http_profile

    return trtc_client.TrtcClient(cred, "ap-beijing", client_profile)


def clone_voice(client):
    """
    Clone a voice with the flow_01_ex model.

    Returns:
        Cloned VoiceId, or None on failure.
    """
    if not os.path.exists(CLONE_AUDIO_FILE):
        print(f"Error: clone audio file not found: {CLONE_AUDIO_FILE}")
        return None

    with open(CLONE_AUDIO_FILE, "rb") as f:
        audio_base64 = base64.b64encode(f.read()).decode("utf-8")

    params = {
        "Model": MODEL,
        "SdkAppId": SDK_APP_ID,
        "VoiceName": VOICE_NAME,
        "PromptAudio": audio_base64,
    }
    if PROMPT_TEXT:
        params["PromptText"] = PROMPT_TEXT
    if CLONE_LANGUAGE:
        params["Language"] = CLONE_LANGUAGE

    req = models.VoiceCloneRequest()
    req.from_json_string(json.dumps(params))

    print("=" * 60)
    print("Step 1: Voice Clone")
    print("=" * 60)
    print(f"Model: {MODEL}")
    print(f"Audio: {CLONE_AUDIO_FILE}")
    print(f"VoiceName: {VOICE_NAME}")

    try:
        resp = client.VoiceClone(req)
        print("Voice cloned successfully!")
        print(f"VoiceId: {resp.VoiceId}")
        print(f"RequestId: {getattr(resp, 'RequestId', 'N/A')}")
        return resp.VoiceId
    except TencentCloudSDKException as e:
        print("Voice cloning failed!")
        print(f"Error Code: {e.code}")
        print(f"Error Message: {e.message}")
        print(f"Request ID: {e.requestId}")
        return None
    except Exception as e:
        print(f"Voice cloning failed: {e}")
        return None


def save_audio_file(audio_data, voice_id):
    """Save synthesized audio to examples/python."""
    output_dir = os.path.dirname(os.path.abspath(__file__))
    filename = f"flow_01_ex_{voice_id}_{int(time.time())}.{AUDIO_FORMAT['Format']}"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "wb") as f:
        f.write(audio_data)

    print(f"Audio saved to: {filepath}")
    return filepath


def text_to_speech(client, voice_id):
    """
    Run non-streaming TTS inference with the cloned voice.

    Returns:
        Path to the saved audio file, or None on failure.
    """
    voice = {
        "VoiceId": voice_id,
        **VOICE_PARAMS,
        "Language": INFERENCE_LANGUAGE,
    }

    params = {
        "Model": MODEL,
        "Text": INFERENCE_TEXT,
        "Voice": voice,
        "AudioFormat": AUDIO_FORMAT,
        "SdkAppId": SDK_APP_ID,
    }

    req = models.TextToSpeechRequest()
    req.from_json_string(json.dumps(params))

    print("\n" + "=" * 60)
    print("Step 2: TextToSpeech Inference")
    print("=" * 60)
    print(f"Model: {MODEL}")
    print(f"VoiceId: {voice_id}")
    print(f"Text: {INFERENCE_TEXT}")
    print(f"Format: {AUDIO_FORMAT['Format']}")

    try:
        start_time = time.time()
        resp = client.TextToSpeech(req)
        elapsed_ms = (time.time() - start_time) * 1000

        if not getattr(resp, "Audio", None):
            print("Error: no audio data in response")
            return None

        audio_data = base64.b64decode(resp.Audio)
        print("TTS inference successful!")
        print(f"RequestId: {getattr(resp, 'RequestId', 'N/A')}")
        print(f"Audio size: {len(audio_data)} bytes")
        print(f"Time elapsed: {elapsed_ms:.0f}ms")
        return save_audio_file(audio_data, voice_id)
    except TencentCloudSDKException as e:
        print("TTS inference failed!")
        print(f"Error Code: {e.code}")
        print(f"Error Message: {e.message}")
        print(f"Request ID: {e.requestId}")
        return None
    except Exception as e:
        print(f"TTS inference failed: {e}")
        return None


def main():
    client = create_client()
    if not client:
        return

    voice_id = clone_voice(client)
    if not voice_id:
        return

    text_to_speech(client, voice_id)


if __name__ == "__main__":
    main()
