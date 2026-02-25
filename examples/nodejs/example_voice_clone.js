#!/usr/bin/env node
/**
 * FlowTTS Voice Clone Example
 *
 * Corresponds to examples/python/example_voice_clone.py
 *
 * Note: Voice Clone and Non-streaming APIs use endpoint "trtc.tencentcloudapi.com",
 * while Streaming SSE API uses "trtc.ai.tencentcloudapi.com".
 */

import { readFileSync } from "fs";
import { resolve } from "path";
import { loadConfig, createClient, projectRoot } from "./utils.js";

// ========== Configuration ==========
const MODEL = "flow_01_turbo";
const CLONE_AUDIO_FILE = resolve(
  projectRoot(),
  "test_data/clone_sample.wav"
); // 16kHz mono WAV, 10-180 seconds
const VOICE_NAME = "MyClonedVoice";
// (Optional) Transcript of the reference audio, improves clone quality
const PROMPT_TEXT = "";
// (Optional) Language of the reference audio (ISO 639-1): zh/en/yue/ja/ko/ar/id/th, default auto
const LANGUAGE = "";
// ====================================

async function voiceClone(client, audioFile, voiceName, sdkAppId) {
  // Read and encode audio file
  const audioData = readFileSync(audioFile);
  const audioBase64 = audioData.toString("base64");

  const params = {
    Model: MODEL,
    SdkAppId: sdkAppId,
    VoiceName: voiceName,
    PromptAudio: audioBase64,
  };
  // Optional: provide transcript of the reference audio for better quality
  if (PROMPT_TEXT) {
    params.PromptText = PROMPT_TEXT;
  }
  // Optional: specify language (ISO 639-1)
  if (LANGUAGE) {
    params.Language = LANGUAGE;
  }

  console.log(`Cloning voice: ${voiceName}`);

  try {
    const resp = await client.VoiceClone(params);
    const voiceId = resp.VoiceId;

    console.log(`Voice cloned successfully!`);
    console.log(`Voice ID: ${voiceId}`);
    console.log(`\nNext: Use this voice_id in example_streaming.js`);
    console.log(`Update VOICE_CONFIG:`);
    console.log(`  "VoiceId": "${voiceId}"`);
    return voiceId;
  } catch (e) {
    console.log(`Voice cloning failed!`);
    if (e.code) {
      console.log(`Error Code: ${e.code}`);
      console.log(`Error Message: ${e.message}`);
      console.log(`Request ID: ${e.requestId}`);
    } else {
      console.log(`Error: ${e.message}`);
    }
    return null;
  }
}

async function main() {
  const cfg = loadConfig();
  // Voice Clone API uses trtc.tencentcloudapi.com
  // (Streaming SSE API uses trtc.ai.tencentcloudapi.com)
  const client = createClient(cfg, "trtc.tencentcloudapi.com");

  await voiceClone(client, CLONE_AUDIO_FILE, VOICE_NAME, cfg.sdkAppId);
}

main().catch(console.error);
