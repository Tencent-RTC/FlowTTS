#!/usr/bin/env node
/**
 * FlowTTS Non-Streaming Example - TextToSpeech with MP3/PCM support
 *
 * Corresponds to examples/python/example_non_streaming.py
 *
 * API Reference:
 * - https://cloud.tencent.com/document/api/647/122475
 * - https://cloud.tencent.com/document/api/647/44055#AudioFormat
 */

import { writeFileSync } from "fs";
import { dirname } from "path";
import { fileURLToPath } from "url";
import { join } from "path";
import { loadConfig, createClient, pcmToWav } from "./utils.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ========== Configuration ==========
const MODEL = "flow_01_turbo";

const VOICE_CONFIG = {
  VoiceId: "v-female-R2s4N9qJ",
  Speed: 1.0,
  Volume: 1.0,
  Pitch: 0,
};

const LANGUAGE = "zh"; // Language: zh/en/yue/ja/ko/ar/id/th, default auto

const AUDIO_FORMAT = {
  Format: "mp3", // "mp3" or "pcm"
  SampleRate: 24000,
};
// ====================================

function saveAudioFile(audioData, filename) {
  const filepath = join(__dirname, filename);
  writeFileSync(filepath, audioData);
  console.log(`   Audio saved to: ${filepath}`);
  return filepath;
}

async function textToSpeechNonStreaming(
  client,
  sdkAppId,
  text = "欢迎使用腾讯云语音合成服务，祝您使用愉快！",
  audioFormat = "mp3"
) {
  console.log(`\nStarting TTS synthesis`);
  console.log(`   Voice: ${VOICE_CONFIG.VoiceId}`);
  console.log(`   Text: ${text}`);
  console.log(`   Text length: ${text.length}`);
  console.log(`   Format: ${audioFormat}`);
  console.log(`   SdkAppId: ${sdkAppId}`);

  const params = {
    Model: MODEL,
    Text: text,
    Voice: VOICE_CONFIG,
    AudioFormat: {
      Format: audioFormat,
      SampleRate: AUDIO_FORMAT.SampleRate,
    },
    SdkAppId: sdkAppId,
    Language: LANGUAGE,
  };

  const startTime = Date.now();
  const resp = await client.TextToSpeech(params);
  const elapsed = Date.now() - startTime;

  if (resp.Audio) {
    const audioData = Buffer.from(resp.Audio, "base64");

    console.log(`   RequestId: ${resp.RequestId || "N/A"}`);

    let result;
    if (audioFormat === "mp3") {
      console.log(`   MP3 data size: ${audioData.length} bytes`);
      console.log(`   Time elapsed: ${elapsed}ms`);
      const filename = `tts_${VOICE_CONFIG.VoiceId}_${Date.now()}.mp3`;
      result = saveAudioFile(audioData, filename);
    } else {
      const wavData = pcmToWav(audioData, AUDIO_FORMAT.SampleRate);
      console.log(`   WAV data size: ${wavData.length} bytes`);
      console.log(`   Time elapsed: ${elapsed}ms`);
      const filename = `tts_${VOICE_CONFIG.VoiceId}_${Date.now()}.wav`;
      result = saveAudioFile(wavData, filename);
    }

    console.log(`\nTTS synthesis successful!`);
    return result;
  } else {
    console.log("Error: No audio data in response");
    return null;
  }
}

async function main() {
  const cfg = loadConfig();
  // Non-streaming API uses trtc.tencentcloudapi.com
  // (Streaming SSE API uses trtc.ai.tencentcloudapi.com)
  const client = createClient(cfg, "trtc.tencentcloudapi.com");

  // Example 1: MP3 format (default)
  console.log("=".repeat(50));
  console.log("Example 1: MP3 Format");
  console.log("=".repeat(50));
  await textToSpeechNonStreaming(
    client,
    cfg.sdkAppId,
    "欢迎使用腾讯云FlowTTS，这是MP3格式输出。",
    "mp3"
  );

  // Example 2: PCM format (converted to WAV)
  console.log("\n" + "=".repeat(50));
  console.log("Example 2: PCM Format (saved as WAV)");
  console.log("=".repeat(50));
  await textToSpeechNonStreaming(
    client,
    cfg.sdkAppId,
    "欢迎使用腾讯云FlowTTS，这是PCM格式输出。",
    "pcm"
  );
}

main().catch(console.error);
