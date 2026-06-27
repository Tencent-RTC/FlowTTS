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
import WebSocket from "ws";
import { loadConfig } from "./utils.js";

const HOST = "flowtts.cloud.tencent.com";

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

  const queryString = Object.entries(params)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`)
    .join("&");

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
      const audioLen = (data.Audio || "").length;
      console.log(`收到句子: ${data.Sentence} (音频: ${audioLen} 字符)`);
    } else if (event === "SessionEnd") {
      const data = msg.Data || {};
      console.log(
        `会话结束 - 句子数: ${data.TotalSentences}, 时长: ${data.TotalDuration}秒`
      );
      this.ws.close();
    } else if (event === "SessionError") {
      const data = msg.Data || {};
      console.log(`会话错误: ${data.ErrorCode} - ${data.ErrorMessage}`);
    } else if (event === "SentenceError") {
      const data = msg.Data || {};
      console.log(`句子错误: ${JSON.stringify(data)}`);
    }
  }

  async startSession() {
    const message = {
      Event: "StartSession",
      ConnectionId: this.connectionId,
      SessionId: "",
      MessageId: crypto.randomUUID(),
      Data: {
        Voice: {
          VoiceId: "v-male-s5NqE0rZ",
        },
      },
    };

    this.ws.send(JSON.stringify(message));
    console.log("已发送StartSession");
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
