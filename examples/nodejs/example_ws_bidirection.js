#!/usr/bin/env node
/**
 * FlowTTS WebSocket Bidirectional Streaming Example
 *
 * Corresponds to examples/python/example_ws_bidirection.py
 *
 * This example does NOT use the Tencent Cloud SDK.
 * It implements the WebSocket protocol directly using the "ws" library.
 */

import crypto from "crypto";
import fs from "fs";
import WebSocket from "ws";
import { loadConfig } from "./utils.js";

const HOST = "flowtts.cloud.tencent.com";

// TTS 模型：留空使用服务端默认（flow_02_turbo），也可显式指定
const MODEL = process.env.FLOW_TTS_MODEL || "flow_02_turbo";
const VOICE_ID = process.env.FLOW_TTS_VOICE_ID || "v-male-s5NqE0rZ";

// 音频格式：pcm / mp3 / opus（opus 为 Ogg 封装，每句一条独立 Ogg 流）
const AUDIO_FORMAT = process.env.FLOW_TTS_FORMAT || "pcm";
const SAMPLE_RATE = parseInt(process.env.FLOW_TTS_SAMPLE_RATE || "24000", 10);
const BIT_RATE = parseInt(process.env.FLOW_TTS_BITRATE || "128", 10); // 仅 mp3 生效

// 保存文件的扩展名：pcm 会补上 WAV 头，opus 保存为 .ogg
const FILE_EXT = { pcm: "wav", mp3: "mp3", opus: "ogg" };

/** 给裸 PCM 数据补上 WAV 头 */
function pcmToWav(pcm, sampleRate, channels = 1, bits = 16) {
  const byteRate = (sampleRate * channels * bits) / 8;
  const blockAlign = (channels * bits) / 8;
  const header = Buffer.alloc(44);
  header.write("RIFF", 0);
  header.writeUInt32LE(36 + pcm.length, 4);
  header.write("WAVEfmt ", 8);
  header.writeUInt32LE(16, 16);
  header.writeUInt16LE(1, 20);
  header.writeUInt16LE(channels, 22);
  header.writeUInt32LE(sampleRate, 24);
  header.writeUInt32LE(byteRate, 28);
  header.writeUInt16LE(blockAlign, 32);
  header.writeUInt16LE(bits, 34);
  header.write("data", 36);
  header.writeUInt32LE(pcm.length, 40);
  return Buffer.concat([header, pcm]);
}

function generateSignature(params, secretKey) {
  const sortedParams = Object.entries(params).sort(([a], [b]) =>
    a.localeCompare(b)
  );
  let signStr = `GET${HOST}/api/v1/flow_tts/bidirection?`;
  signStr += sortedParams.map(([k, v]) => `${k}=${v}`).join("&");

  const hmac = crypto.createHmac("sha1", secretKey);
  hmac.update(signStr);
  return hmac.digest("base64");
}

function generateUrl(cfg) {
  const connectionId = crypto.randomUUID();
  const timestamp = Math.floor(Date.now() / 1000);

  const params = {
    Action: "TextToSpeechBidirection",
    SecretId: cfg.secretId,
    SdkAppId: cfg.sdkAppId,
    Timestamp: timestamp,
    Expired: timestamp + 86400,
    ConnectionId: connectionId,
  };

  params.Signature = generateSignature(params, cfg.secretKey);

  const sortedEntries = Object.entries(params).sort(([a], [b]) =>
    a.localeCompare(b)
  );
  const queryString = new URLSearchParams(
    sortedEntries.map(([k, v]) => [k, String(v)])
  ).toString();

  const url = `wss://${HOST}/api/v1/flow_tts/bidirection?${queryString}`;
  return { url, connectionId };
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

class TTSWebSocketClient {
  constructor() {
    this.ws = null;
    this.connectionId = null;
    this.sessionId = null;
    this.audioChunks = []; // 收到的音频分片，按到达顺序拼接
  }

  connect(cfg) {
    return new Promise((resolve, reject) => {
      const { url, connectionId } = generateUrl(cfg);
      this.connectionId = connectionId;
      console.log(`连接URL: ${url}`);

      this.ws = new WebSocket(url);

      this.ws.on("open", async () => {
        console.log("WebSocket连接已建立");
        await this.startSession();
      });

      this.ws.on("message", async (data) => {
        await this.handleMessage(data.toString());
      });

      this.ws.on("error", (err) => {
        console.log(`WebSocket错误: ${err.message}`);
        reject(err);
      });

      this.ws.on("close", () => {
        console.log("WebSocket连接已关闭");
        resolve();
      });
    });
  }

  async handleMessage(message) {
    const msg = JSON.parse(message);
    const event = msg.Event;
    console.log(`\n收到事件: ${event}`);

    if (event === "SessionStart") {
      this.sessionId = msg.SessionId;
      console.log(`会话已开始，SessionId: ${this.sessionId}`);
      // Start sending text stream (non-blocking)
      this.sendTextStream().catch(console.error);
    } else if (event === "SentenceAudio") {
      const data = msg.Data || {};
      const audio = Buffer.from(data.Audio || "", "base64");
      if (audio.length > 0) {
        this.audioChunks.push(audio);
      }
      console.log(
        `收到句子[${data.SentenceId}]: ${data.Sentence} (音频: ${audio.length} 字节, IsEnd=${data.IsEnd})`
      );
    } else if (event === "SessionEnd") {
      const data = msg.Data || {};
      console.log(
        `会话结束 - 句子数: ${data.TotalSentences}, 时长: ${data.TotalDuration}秒`
      );
      this.saveAudio();
      this.ws.close();
    } else if (event === "SessionError") {
      const data = msg.Data || {};
      console.log(`会话错误: ${data.ErrorCode} - ${data.ErrorMessage}`);
    } else if (event === "SentenceError") {
      const data = msg.Data || {};
      console.log(`句子错误: ${JSON.stringify(data)}`);
    }
  }

  /** 把收到的音频分片拼接落盘 */
  saveAudio() {
    if (this.audioChunks.length === 0) return;
    let data = Buffer.concat(this.audioChunks);
    if (AUDIO_FORMAT === "pcm") {
      data = pcmToWav(data, SAMPLE_RATE);
    }
    const ext = FILE_EXT[AUDIO_FORMAT] || AUDIO_FORMAT;
    const filename = `ws_bidirection_${VOICE_ID}_${Math.floor(Date.now() / 1000)}.${ext}`;
    fs.writeFileSync(filename, data);
    console.log(`音频已保存: ${filename} (${data.length} 字节)`);
    if (AUDIO_FORMAT === "opus") {
      // 每句是一条独立的 Ogg 流，直接拼接得到 chained Ogg：
      // ffmpeg / VLC 可正常播放，部分浏览器只会播第一段，需要时转码即可
      console.log(`提示: 如需单流文件可执行 ffmpeg -i ${filename} out.wav`);
    }
  }

  async startSession() {
    const message = {
      Event: "StartSession",
      ConnectionId: this.connectionId,
      SessionId: "",
      MessageId: crypto.randomUUID(),
      Data: {
        Language: "zh",
        Model: MODEL,
        AudioFormat: {
          Format: AUDIO_FORMAT,
          SampleRate: SAMPLE_RATE,
          BitRate: BIT_RATE,
        },
        Voice: {
          VoiceId: VOICE_ID,
          Speed: 1.0,
          Volume: 1.0,
          Pitch: 0,
        },
      },
    };

    this.ws.send(JSON.stringify(message));
    console.log(
      `已发送StartSession (Model=${MODEL}, VoiceId=${VOICE_ID}, Format=${AUDIO_FORMAT}, SampleRate=${SAMPLE_RATE})`
    );
  }

  async sendTextStream() {
    const texts = [
      "今天天气",
      "真好！",
      "你那边",
      "怎么样？",
      "我这边阳光明媚。",
    ];

    for (let i = 0; i < texts.length; i++) {
      await sleep(1000);
      const message = {
        Event: "ContinueSession",
        ConnectionId: this.connectionId,
        SessionId: this.sessionId,
        MessageId: crypto.randomUUID(),
        Data: { Text: texts[i] },
      };
      this.ws.send(JSON.stringify(message));
      console.log(`已发送文本 [${i + 1}/${texts.length}]: ${texts[i]}`);
    }

    await sleep(1000);
    await this.finishSession();
  }

  async finishSession() {
    const message = {
      Event: "FinishSession",
      ConnectionId: this.connectionId,
      SessionId: this.sessionId,
      MessageId: crypto.randomUUID(),
      Data: {},
    };
    this.ws.send(JSON.stringify(message));
    console.log("已发送FinishSession");
  }
}

async function main() {
  const cfg = loadConfig();
  const client = new TTSWebSocketClient();
  await client.connect(cfg);
}

main().catch(console.error);
