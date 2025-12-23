#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlowTTS Voice Clone Example
"""

import os
import json
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
SDK_APP_ID = int(os.getenv("TENCENTCLOUD_SDK_APP_ID", "1400000000"))
MODEL = "flow_01_turbo"

# Voice clone settings
CLONE_AUDIO_FILE = "./test_data/clone_sample.wav"  # 16kHz mono WAV, 10-180 seconds
VOICE_NAME = "MyClonedVoice"
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
        "trtc.tencentcloudapi.com"
    )
    http_profile.reqTimeout = 120
    http_profile.keepAlive = True        # Enable Keep-Alive
    http_profile.pre_conn_pool_size = 3  # Connection pool size

    client_profile = ClientProfile()
    client_profile.httpProfile = http_profile

    return trtc_client.TrtcClient(cred, "ap-beijing", client_profile)


def voice_clone(client, audio_file, voice_name):
    """
    Clone voice from audio sample.

    Args:
        client: TRTC client instance
        audio_file: Path to audio file (16kHz mono WAV, 10-180 seconds)
        voice_name: Name for the cloned voice

    Returns:
        voice_id: Cloned voice ID
    """
    # Read and encode audio file
    with open(audio_file, 'rb') as f:
        audio_data = f.read()
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')

    # Create clone request
    req = models.VoiceCloneRequest()
    params = {
        "Model": MODEL,
        "SdkAppId": SDK_APP_ID,
        "VoiceName": voice_name,
        "PromptAudio": audio_base64
    }
    req.from_json_string(json.dumps(params))

    print(f"Cloning voice: {voice_name}")

    # Execute cloning
    try:
        resp = client.VoiceClone(req)
        voice_id = resp.VoiceId

        print(f"Voice cloned successfully!")
        print(f"Voice ID: {voice_id}")
        print(f"\nNext: Use this voice_id in example_simple.py")
        print(f"Update VOICE_CONFIG:")
        print(f'  "VoiceId": "{voice_id}"')
        return voice_id

    except TencentCloudSDKException as e:
        print(f"Voice cloning failed!")
        print(f"Error Code: {e.code}")
        print(f"Error Message: {e.message}")
        print(f"Request ID: {e.requestId}")
        return None
    except Exception as e:
        print(f"Voice cloning failed: {e}")
        return None


def main():
    # Create client (reuse for multiple requests)
    client = create_client()

    # Clone voice from audio sample
    voice_clone(client, CLONE_AUDIO_FILE, VOICE_NAME)


if __name__ == "__main__":
    main()
