#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
播客 TTS 合成辅助脚本

读取播客脚本 JSON 文件（由 podcast-generate skill 生成），
逐轮调用 FlowTTS 流式 API 合成语音，最终拼接为完整的播客 WAV 音频。

用法:
    # 在项目根目录执行（需要 .env 文件中的环境变量）
    python .claude/skills/podcast-generate/scripts/synthesize_podcast.py -i talk_about_ai.podcast.json -o talk_about_ai.wav

依赖:
    pip install python-dotenv tencentcloud-sdk-python
"""

import os
import sys
import io
import json
import wave
import time
import base64
import argparse
from pathlib import Path

from dotenv import load_dotenv
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.trtc.v20190722 import trtc_client, models


# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
MODEL = "flow_01_turbo"
CHANNELS = 1           # 单声道
SAMPLE_WIDTH = 2       # 16-bit (2 bytes per sample)
SILENCE_DURATION_MS = 300  # 对话轮次间的静音时长（毫秒）


# ---------------------------------------------------------------------------
# 环境与客户端
# ---------------------------------------------------------------------------

def check_env():
    """
    检查必要的环境变量是否已配置。
    缺失时打印提示并退出。
    """
    required = ["TENCENTCLOUD_SECRET_ID", "TENCENTCLOUD_SECRET_KEY"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        print(f"[错误] 以下环境变量未配置: {', '.join(missing)}")
        print("请在项目根目录的 .env 文件中配置，或通过 export 设置。")
        sys.exit(1)

    # SDK_APP_ID 有默认值，但给出提示
    sdk_app_id_raw = os.getenv("TENCENTCLOUD_SDK_APP_ID") or os.getenv("SDKAPPID")
    if not sdk_app_id_raw:
        print("[警告] 未检测到 TENCENTCLOUD_SDK_APP_ID / SDKAPPID，将使用默认值 1400000000")


def get_sdk_app_id():
    """获取 SDK_APP_ID，优先从环境变量读取。"""
    return int(
        os.getenv("TENCENTCLOUD_SDK_APP_ID")
        or os.getenv("SDKAPPID")
        or "1400000000"
    )


def create_client():
    """
    创建腾讯云 TRTC 客户端，启用 Keep-Alive 以复用 TCP 连接。
    """
    cred = credential.Credential(
        os.getenv("TENCENTCLOUD_SECRET_ID"),
        os.getenv("TENCENTCLOUD_SECRET_KEY"),
    )

    http_profile = HttpProfile()
    # 流式 SSE API 使用 trtc.ai.tencentcloudapi.com
    http_profile.endpoint = "trtc.ai.tencentcloudapi.com"
    http_profile.reqTimeout = 120
    http_profile.keepAlive = True
    http_profile.pre_conn_pool_size = 3

    client_profile = ClientProfile()
    client_profile.httpProfile = http_profile

    return trtc_client.TrtcClient(cred, "ap-beijing", client_profile)


# ---------------------------------------------------------------------------
# TTS 核心
# ---------------------------------------------------------------------------

def synthesize_turn(client, text, voice_config, sample_rate):
    """
    调用 FlowTTS 流式 SSE API 合成单轮文本为 PCM 音频数据。

    Args:
        client:       TRTC 客户端实例
        text:         待合成文本
        voice_config: 语音配置字典（含 VoiceId、Speed 等）
        sample_rate:  采样率

    Returns:
        bytes: 原始 PCM 数据；合成失败时返回 b''
    """
    audio_format = {
        "Format": "pcm",
        "SampleRate": sample_rate,
    }

    req = models.TextToSpeechSSERequest()
    params = {
        "Model": MODEL,
        "Text": text,
        "Voice": voice_config,
        "AudioFormat": audio_format,
        "SdkAppId": get_sdk_app_id(),
    }
    req.from_json_string(json.dumps(params))

    resp = client.TextToSpeechSSE(req)

    audio_chunks = []
    for event in resp:
        if isinstance(event, dict) and "data" in event:
            try:
                data = json.loads(event["data"].strip())
                if data.get("Type") == "audio" and data.get("Audio"):
                    audio_chunks.append(base64.b64decode(data["Audio"]))
                if data.get("IsEnd"):
                    break
            except (json.JSONDecodeError, KeyError):
                continue

    return b"".join(audio_chunks)


def generate_silence(duration_ms, sample_rate):
    """
    生成指定时长的静音 PCM 数据（16-bit、单声道、全零）。

    Args:
        duration_ms: 静音时长（毫秒）
        sample_rate: 采样率

    Returns:
        bytes: 静音 PCM 数据
    """
    num_samples = int(sample_rate * duration_ms / 1000)
    # 16-bit 单声道：每个采样 2 字节，静音为全零
    return b"\x00\x00" * num_samples


def pcm_to_wav(pcm_data, sample_rate, channels=CHANNELS, sample_width=SAMPLE_WIDTH):
    """
    将原始 PCM 数据转换为带 WAV 头的音频数据。

    Args:
        pcm_data:     原始 PCM 字节
        sample_rate:  采样率
        channels:     声道数（默认 1）
        sample_width: 每采样字节数（默认 2，即 16-bit）

    Returns:
        bytes: 完整的 WAV 文件数据
    """
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    return wav_buffer.getvalue()


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def build_voice_config(voice_id, speed=1.0, volume=1.0, pitch=0, language="zh"):
    """
    构建 FlowTTS Voice 配置字典。

    Args:
        voice_id: 语音 ID
        speed:    语速 [0.5, 2.0]
        volume:   音量 (0, 10]
        pitch:    音调 [-12, 12]
        language: 语言 zh/en/yue/ja/ko/ar/id/th

    Returns:
        dict: Voice 配置
    """
    return {
        "VoiceId": voice_id,
        "Speed": speed,
        "Volume": volume,
        "Pitch": pitch,
        "Language": language,
    }


def synthesize_podcast(input_path, output_path, voice_a_id, voice_b_id, sample_rate):
    """
    读取播客脚本 JSON 并逐轮合成语音，最终拼接输出为 WAV 文件。

    Args:
        input_path:  播客脚本 JSON 文件路径
        output_path: 输出 WAV 文件路径
        voice_a_id:  Speaker A 的 VoiceId
        voice_b_id:  Speaker B 的 VoiceId
        sample_rate: 采样率
    """
    # ---- 1. 读取 JSON 脚本 ----
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"[错误] 播客脚本文件不存在: {input_file}")
        sys.exit(1)

    with open(input_file, "r", encoding="utf-8") as f:
        script = json.load(f)

    dialogue = script.get("dialogue", [])
    if not dialogue:
        print("[错误] 播客脚本中未找到 dialogue 数组，或数组为空。")
        sys.exit(1)

    title = script.get("title", "未知标题")
    print(f"播客标题: {title}")
    print(f"对话轮次: {len(dialogue)}")
    print(f"采样率:   {sample_rate} Hz")
    print(f"Speaker A VoiceId: {voice_a_id}")
    print(f"Speaker B VoiceId: {voice_b_id}")
    print("-" * 50)

    # ---- 2. 构建 voice config ----
    voice_config_a = build_voice_config(voice_a_id)
    voice_config_b = build_voice_config(voice_b_id)

    # ---- 3. 创建客户端 ----
    client = create_client()

    # ---- 4. 逐轮合成 ----
    silence_pcm = generate_silence(SILENCE_DURATION_MS, sample_rate)
    all_pcm_segments = []
    total = len(dialogue)
    success_count = 0
    fail_count = 0

    for idx, turn in enumerate(dialogue, start=1):
        speaker = turn.get("speaker", "?")
        text = turn.get("text", "")

        if not text.strip():
            print(f"  [{idx}/{total}] Speaker {speaker} - 文本为空，跳过")
            continue

        # 选择对应的语音配置
        if speaker == "A":
            voice_config = voice_config_a
        elif speaker == "B":
            voice_config = voice_config_b
        else:
            # 未知 speaker，默认使用 A 的配置
            print(f"  [{idx}/{total}] 未知 Speaker '{speaker}'，使用 Speaker A 配置")
            voice_config = voice_config_a

        # 截断过长文本用于显示
        display_text = text if len(text) <= 40 else text[:40] + "..."
        print(f"  [{idx}/{total}] Speaker {speaker}: {display_text}")

        try:
            start_time = time.time()
            pcm_data = synthesize_turn(client, text, voice_config, sample_rate)
            elapsed = time.time() - start_time

            if pcm_data:
                all_pcm_segments.append(pcm_data)
                success_count += 1
                duration_s = len(pcm_data) / (sample_rate * SAMPLE_WIDTH * CHANNELS)
                print(f"           -> 合成成功 ({duration_s:.1f}s 音频, 耗时 {elapsed:.1f}s)")
            else:
                fail_count += 1
                print(f"           -> [警告] 未收到音频数据，跳过此轮")

        except Exception as e:
            fail_count += 1
            print(f"           -> [警告] 合成失败: {e}")

        # 在每轮之间插入静音（最后一轮不插入）
        if idx < total:
            all_pcm_segments.append(silence_pcm)

    # ---- 5. 拼接并保存 WAV ----
    print("-" * 50)

    if not all_pcm_segments:
        print("[错误] 没有成功合成任何音频片段，无法生成输出文件。")
        sys.exit(1)

    combined_pcm = b"".join(all_pcm_segments)
    wav_data = pcm_to_wav(combined_pcm, sample_rate)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "wb") as f:
        f.write(wav_data)

    total_duration_s = len(combined_pcm) / (sample_rate * SAMPLE_WIDTH * CHANNELS)
    print(f"合成完成!")
    print(f"  成功: {success_count} 轮 / 失败: {fail_count} 轮 / 总计: {total} 轮")
    print(f"  音频时长:  {total_duration_s:.1f} 秒 ({total_duration_s / 60:.1f} 分钟)")
    print(f"  PCM 大小:  {len(combined_pcm):,} bytes")
    print(f"  WAV 大小:  {len(wav_data):,} bytes")
    print(f"  输出文件:  {output_file.resolve()}")


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="播客 TTS 合成脚本 - 读取播客脚本 JSON，调用 FlowTTS API 合成完整播客音频",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  python synthesize_podcast.py -i talk_about_ai.podcast.json -o talk_about_ai.wav
  python synthesize_podcast.py --voice-a v-male-Zl2mKB1o --voice-b v-female-R2s4N9qJ
  python synthesize_podcast.py -i my_script.json --sample-rate 16000

播客脚本 JSON 格式:
  {
    "title": "...",
    "dialogue": [
      {"speaker": "A", "text": "..."},
      {"speaker": "B", "text": "..."}
    ]
  }
""",
    )

    parser.add_argument(
        "-i", "--input",
        default="podcast_script.json",
        help="播客脚本 JSON 文件路径 (默认: podcast_script.json)",
    )
    parser.add_argument(
        "-o", "--output",
        default="podcast_output.wav",
        help="输出音频文件路径 (默认: podcast_output.wav)",
    )
    parser.add_argument(
        "--voice-a",
        default="v-male-Zl2mKB1o",
        help="Speaker A 的 VoiceId (默认: v-male-Zl2mKB1o)",
    )
    parser.add_argument(
        "--voice-b",
        default="v-female-R2s4N9qJ",
        help="Speaker B 的 VoiceId (默认: v-female-R2s4N9qJ)",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=24000,
        choices=[16000, 24000],
        help="采样率 (默认: 24000, 可选: 16000 或 24000)",
    )

    return parser.parse_args()


def main():
    """主入口函数。"""
    # 加载 .env（在项目根目录执行时自动读取）
    load_dotenv()

    args = parse_args()

    # 检查环境变量
    check_env()

    print("=" * 50)
    print("  FlowTTS 播客音频合成")
    print("=" * 50)

    synthesize_podcast(
        input_path=args.input,
        output_path=args.output,
        voice_a_id=args.voice_a,
        voice_b_id=args.voice_b,
        sample_rate=args.sample_rate,
    )


if __name__ == "__main__":
    main()
