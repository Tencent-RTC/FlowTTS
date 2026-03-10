#!/usr/bin/env node
/**
 * FlowTTS Streaming Example - SSE Streaming TTS
 *
 * Corresponds to examples/python/example_streaming.py
 */

import { writeFileSync } from "fs";
import { loadConfig, createClient, pcmToWav } from "./utils.js";

// ========== Configuration ==========
const MODEL = ""; // Empty string uses the latest model by default

const VOICE_CONFIG = {
  VoiceId: "v-female-R2s4N9qJ",
  Speed: 1.0,
  Volume: 1.0,
  Pitch: 0,
};

const LANGUAGE = "zh"; // Language: zh/en/yue/ja/ko/ar/id/th, default auto

const AUDIO_FORMAT = {
  Format: "pcm", // Streaming SSE only supports pcm
  SampleRate: 24000,
};
// ====================================

async function textToSpeech(client, text, sdkAppId, outputFile = "output.wav") {
  const params = {
    Model: MODEL,
    Text: text,
    Voice: VOICE_CONFIG,
    AudioFormat: AUDIO_FORMAT,
    SdkAppId: sdkAppId,
    Language: LANGUAGE,
  };

  console.log(`Synthesizing: ${text}`);

  const resp = await client.TextToSpeechSSE(params);

  const audioChunks = [];
  for await (const event of resp) {
    try {
      const data =
        typeof event.data === "string"
          ? JSON.parse(event.data)
          : event.data || event;

      if (data.Type === "audio" && data.Audio) {
        audioChunks.push(Buffer.from(data.Audio, "base64"));
      }
      if (data.IsEnd) {
        break;
      }
    } catch {
      continue;
    }
  }

  if (audioChunks.length > 0) {
    const pcmData = Buffer.concat(audioChunks);
    const wavData = pcmToWav(pcmData, AUDIO_FORMAT.SampleRate);

    writeFileSync(outputFile, wavData);
    console.log(`Audio saved to: ${outputFile}`);
    console.log(`PCM size: ${pcmData.length} bytes, WAV size: ${wavData.length} bytes`);
  } else {
    console.log("No audio data received");
  }
}

async function main() {
  const cfg = loadConfig();
  // Streaming SSE API uses trtc.ai.tencentcloudapi.com (default in utils.js)
  // (Non-streaming and Voice Clone APIs use trtc.tencentcloudapi.com)
  const client = createClient(cfg);

  await textToSpeech(
    client,
    "晚风轻轻吹过窗台，月光洒在你的脸上，愿今夜的星星都化作美梦，伴你安然入睡。晚安，亲爱的。",
    cfg.sdkAppId,
    "output.wav"
  );
}

main().catch(console.error);
