#!/usr/bin/env node
/**
 * FlowTTS flow_01_ex Example - Voice Clone + Inference
 *
 * This example demonstrates the complete flow for the flow_01_ex model:
 * 1. Clone a voice from a reference audio sample.
 * 2. Use the returned VoiceId for non-streaming TTS inference.
 *
 * Voice Clone and non-streaming TTS both use endpoint "trtc.tencentcloudapi.com".
 */

import { readFileSync, writeFileSync, existsSync } from "fs";
import { dirname, join, resolve } from "path";
import { fileURLToPath } from "url";
import { loadConfig, createClient, projectRoot } from "./utils.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ========== Configuration ==========
const MODEL = "flow_01_ex";

// Voice clone settings
const CLONE_AUDIO_FILE = resolve(projectRoot(), "test_data/clone_sample.wav"); // 16kHz mono WAV, 10-180 seconds
const VOICE_NAME = "Flow01ExClonedVoice";
// (Optional) Transcript of the reference audio, improves clone quality
const PROMPT_TEXT = "";
// (Optional) Language of the reference audio (ISO 639-1): zh/en/yue/ja/ko/ar/id/th, default auto
const CLONE_LANGUAGE = "";

// TTS inference settings
const INFERENCE_TEXT =
  "欢迎使用腾讯云 FlowTTS flow_01_ex 模型，这是克隆音色完成后的推理示例。";
const INFERENCE_LANGUAGE = "zh";

const VOICE_PARAMS = {
  Speed: 1.0,
  Volume: 1.0,
  Pitch: 0,
};

const AUDIO_FORMAT = {
  Format: "mp3",
  SampleRate: 24000,
};
// ====================================

async function cloneVoice(client, sdkAppId) {
  if (!existsSync(CLONE_AUDIO_FILE)) {
    console.log(`Error: clone audio file not found: ${CLONE_AUDIO_FILE}`);
    return null;
  }

  const audioBase64 = readFileSync(CLONE_AUDIO_FILE).toString("base64");

  const params = {
    Model: MODEL,
    SdkAppId: sdkAppId,
    VoiceName: VOICE_NAME,
    PromptAudio: audioBase64,
  };
  if (PROMPT_TEXT) {
    params.PromptText = PROMPT_TEXT;
  }
  if (CLONE_LANGUAGE) {
    params.Language = CLONE_LANGUAGE;
  }

  console.log("=".repeat(60));
  console.log("Step 1: Voice Clone");
  console.log("=".repeat(60));
  console.log(`Model: ${MODEL}`);
  console.log(`Audio: ${CLONE_AUDIO_FILE}`);
  console.log(`VoiceName: ${VOICE_NAME}`);

  try {
    const resp = await client.VoiceClone(params);
    console.log("Voice cloned successfully!");
    console.log(`VoiceId: ${resp.VoiceId}`);
    console.log(`RequestId: ${resp.RequestId || "N/A"}`);
    return resp.VoiceId;
  } catch (e) {
    console.log("Voice cloning failed!");
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

function saveAudioFile(audioData, voiceId) {
  const filename = `flow_01_ex_${voiceId}_${Date.now()}.${AUDIO_FORMAT.Format}`;
  const filepath = join(__dirname, filename);
  writeFileSync(filepath, audioData);
  console.log(`Audio saved to: ${filepath}`);
  return filepath;
}

async function textToSpeech(client, sdkAppId, voiceId) {
  const voice = {
    VoiceId: voiceId,
    ...VOICE_PARAMS,
    Language: INFERENCE_LANGUAGE,
  };

  const params = {
    Model: MODEL,
    Text: INFERENCE_TEXT,
    Voice: voice,
    AudioFormat: AUDIO_FORMAT,
    SdkAppId: sdkAppId,
  };

  console.log("\n" + "=".repeat(60));
  console.log("Step 2: TextToSpeech Inference");
  console.log("=".repeat(60));
  console.log(`Model: ${MODEL}`);
  console.log(`VoiceId: ${voiceId}`);
  console.log(`Text: ${INFERENCE_TEXT}`);
  console.log(`Format: ${AUDIO_FORMAT.Format}`);

  try {
    const startTime = Date.now();
    const resp = await client.TextToSpeech(params);
    const elapsed = Date.now() - startTime;

    if (!resp.Audio) {
      console.log("Error: no audio data in response");
      return null;
    }

    const audioData = Buffer.from(resp.Audio, "base64");
    console.log("TTS inference successful!");
    console.log(`RequestId: ${resp.RequestId || "N/A"}`);
    console.log(`Audio size: ${audioData.length} bytes`);
    console.log(`Time elapsed: ${elapsed}ms`);
    return saveAudioFile(audioData, voiceId);
  } catch (e) {
    console.log("TTS inference failed!");
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
  const client = createClient(cfg, "trtc.tencentcloudapi.com");

  const voiceId = await cloneVoice(client, cfg.sdkAppId);
  if (!voiceId) {
    return;
  }

  await textToSpeech(client, cfg.sdkAppId, voiceId);
}

main().catch(console.error);
