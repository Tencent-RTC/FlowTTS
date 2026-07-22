// FlowTTS WebSocket Bidirectional Streaming Example (Go)
//
// Corresponds to examples/python/example_ws_bidirection.py and
// examples/nodejs/example_ws_bidirection.js.
//
// This example does NOT use the Tencent Cloud SDK. It implements the
// WebSocket protocol directly using github.com/gorilla/websocket.
package main

import (
	"crypto/hmac"
	"crypto/sha1"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"sort"
	"strconv"
	"time"

	"flowtts-golang-examples/flowttsutil"

	"github.com/google/uuid"
	"github.com/gorilla/websocket"
)

const host = "flowtts.cloud.tencent.com"

// 保存文件的扩展名：pcm 会补上 WAV 头，opus 保存为 .ogg
var fileExt = map[string]string{"pcm": "wav", "mp3": "mp3", "opus": "ogg"}

func envDefault(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func envInt(key string, fallback int) int {
	if v := os.Getenv(key); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			return n
		}
	}
	return fallback
}

func generateSignature(params map[string]string, secretKey string) string {
	keys := make([]string, 0, len(params))
	for k := range params {
		keys = append(keys, k)
	}
	sort.Strings(keys)

	signStr := "GET" + host + "/api/v1/flow_tts/bidirection?"
	for i, k := range keys {
		if i > 0 {
			signStr += "&"
		}
		signStr += k + "=" + params[k]
	}

	mac := hmac.New(sha1.New, []byte(secretKey))
	mac.Write([]byte(signStr))
	return base64.StdEncoding.EncodeToString(mac.Sum(nil))
}

func generateURL(cfg *flowttsutil.Config) (string, string) {
	connectionID := uuid.NewString()
	timestamp := time.Now().Unix()

	params := map[string]string{
		"Action":       "TextToSpeechBidirection",
		"SecretId":     cfg.SecretID,
		"SdkAppId":     strconv.FormatUint(cfg.SdkAppID, 10),
		"Timestamp":    strconv.FormatInt(timestamp, 10),
		"Expired":      strconv.FormatInt(timestamp+86400, 10),
		"ConnectionId": connectionID,
	}
	params["Signature"] = generateSignature(params, cfg.SecretKey)

	values := url.Values{}
	for k, v := range params {
		values.Set(k, v)
	}
	return "wss://" + host + "/api/v1/flow_tts/bidirection?" + values.Encode(), connectionID
}

type wsMessage struct {
	Event        string                 `json:"Event"`
	ConnectionID string                 `json:"ConnectionId"`
	SessionID    string                 `json:"SessionId"`
	MessageID    string                 `json:"MessageId"`
	Data         map[string]interface{} `json:"Data"`
}

type client struct {
	ws           *websocket.Conn
	connectionID string
	sessionID    string
	model        string
	voiceID      string
	audioFormat  string
	sampleRate   int
	bitRate      int
	texts        []string
	audioChunks  [][]byte // 收到的音频分片，按到达顺序拼接
	done         chan struct{}
}

func (c *client) send(msg wsMessage) error {
	return c.ws.WriteJSON(msg)
}

func (c *client) startSession() error {
	msg := wsMessage{
		Event:        "StartSession",
		ConnectionID: c.connectionID,
		SessionID:    "",
		MessageID:    uuid.NewString(),
		Data: map[string]interface{}{
			"Language": "zh",
			"Model":    c.model,
			"AudioFormat": map[string]interface{}{
				"Format":     c.audioFormat,
				"SampleRate": c.sampleRate,
				"BitRate":    c.bitRate,
			},
			"Voice": map[string]interface{}{
				"VoiceId": c.voiceID,
				"Speed":   1.0,
				"Volume":  1.0,
				"Pitch":   0,
			},
		},
	}
	if err := c.send(msg); err != nil {
		return err
	}
	fmt.Printf("已发送StartSession (Model=%s, VoiceId=%s, Format=%s, SampleRate=%d)\n",
		c.model, c.voiceID, c.audioFormat, c.sampleRate)
	return nil
}

// saveAudio 把收到的音频分片拼接落盘
func (c *client) saveAudio() {
	if len(c.audioChunks) == 0 {
		return
	}
	var data []byte
	for _, chunk := range c.audioChunks {
		data = append(data, chunk...)
	}
	if c.audioFormat == "pcm" {
		data = flowttsutil.PCMToWAV(data, uint32(c.sampleRate), 1, 16)
	}
	ext, ok := fileExt[c.audioFormat]
	if !ok {
		ext = c.audioFormat
	}
	filename := fmt.Sprintf("ws_bidirection_%s_%d.%s", c.voiceID, time.Now().Unix(), ext)
	if err := os.WriteFile(filename, data, 0o644); err != nil {
		fmt.Printf("保存音频失败: %v\n", err)
		return
	}
	fmt.Printf("音频已保存: %s (%d 字节)\n", filename, len(data))
	if c.audioFormat == "opus" {
		// 每句是一条独立的 Ogg 流，直接拼接得到 chained Ogg：
		// ffmpeg / VLC 可正常播放，部分浏览器只会播第一段，需要时转码即可
		fmt.Printf("提示: 如需单流文件可执行 ffmpeg -i %s out.wav\n", filename)
	}
}

func (c *client) sendTextStream() {
	for i, text := range c.texts {
		time.Sleep(1 * time.Second)
		msg := wsMessage{
			Event:        "ContinueSession",
			ConnectionID: c.connectionID,
			SessionID:    c.sessionID,
			MessageID:    uuid.NewString(),
			Data:         map[string]interface{}{"Text": text},
		}
		if err := c.send(msg); err != nil {
			fmt.Printf("发送文本失败: %v\n", err)
			return
		}
		fmt.Printf("已发送文本 [%d/%d]: %s\n", i+1, len(c.texts), text)
	}

	time.Sleep(1 * time.Second)
	c.finishSession()
}

func (c *client) finishSession() {
	msg := wsMessage{
		Event:        "FinishSession",
		ConnectionID: c.connectionID,
		SessionID:    c.sessionID,
		MessageID:    uuid.NewString(),
		Data:         map[string]interface{}{},
	}
	if err := c.send(msg); err != nil {
		fmt.Printf("发送 FinishSession 失败: %v\n", err)
		return
	}
	fmt.Println("已发送FinishSession")
}

func (c *client) handleMessage(raw []byte) {
	var msg struct {
		Event     string          `json:"Event"`
		SessionID string          `json:"SessionId"`
		Data      json.RawMessage `json:"Data"`
	}
	if err := json.Unmarshal(raw, &msg); err != nil {
		fmt.Printf("消息解析失败: %v\n", err)
		return
	}
	fmt.Printf("\n收到事件: %s\n", msg.Event)

	switch msg.Event {
	case "SessionStart":
		c.sessionID = msg.SessionID
		fmt.Printf("会话已开始，SessionId: %s\n", c.sessionID)
		go c.sendTextStream()

	case "SentenceAudio":
		var data struct {
			SentenceID int     `json:"SentenceId"`
			Sentence   string  `json:"Sentence"`
			Audio      string  `json:"Audio"`
			Duration   float64 `json:"Duration"`
			IsEnd      bool    `json:"IsEnd"`
		}
		_ = json.Unmarshal(msg.Data, &data)
		audio, err := base64.StdEncoding.DecodeString(data.Audio)
		if err != nil {
			fmt.Printf("音频解码失败: %v\n", err)
			return
		}
		if len(audio) > 0 {
			c.audioChunks = append(c.audioChunks, audio)
		}
		fmt.Printf("收到句子[%d]: %s (音频: %d 字节, IsEnd=%v)\n",
			data.SentenceID, data.Sentence, len(audio), data.IsEnd)

	case "SessionEnd":
		var data struct {
			TotalSentences int     `json:"TotalSentences"`
			TotalDuration  float64 `json:"TotalDuration"`
			Interrupted    bool    `json:"Interrupted"`
		}
		_ = json.Unmarshal(msg.Data, &data)
		fmt.Printf("会话结束 - 句子数: %d, 时长: %.2f秒\n", data.TotalSentences, data.TotalDuration)
		c.saveAudio()
		_ = c.ws.WriteMessage(websocket.CloseMessage,
			websocket.FormatCloseMessage(websocket.CloseNormalClosure, ""))
		close(c.done)

	case "SessionError":
		fmt.Printf("会话错误: %s\n", string(msg.Data))
		close(c.done)

	case "SentenceError":
		fmt.Printf("句子错误: %s\n", string(msg.Data))
	}
}

func main() {
	cfg, err := flowttsutil.LoadConfig()
	if err != nil {
		panic(err)
	}

	c := &client{
		model:   envDefault("FLOW_TTS_MODEL", "flow_02_turbo"),
		voiceID: envDefault("FLOW_TTS_VOICE_ID", "v-male-s5NqE0rZ"),
		// 音频格式：pcm / mp3 / opus（opus 为 Ogg 封装，每句一条独立 Ogg 流）
		audioFormat: envDefault("FLOW_TTS_FORMAT", "pcm"),
		sampleRate:  envInt("FLOW_TTS_SAMPLE_RATE", 24000),
		bitRate:     envInt("FLOW_TTS_BITRATE", 128), // 仅 mp3 生效
		texts:       []string{"今天天气", "真好！", "你那边", "怎么样？", "我这边阳光明媚。"},
		done:        make(chan struct{}),
	}

	wsURL, connectionID := generateURL(cfg)
	c.connectionID = connectionID
	fmt.Printf("连接URL: %s\n", wsURL)

	ws, resp, err := websocket.DefaultDialer.Dial(wsURL, nil)
	if err != nil {
		if resp != nil {
			fmt.Printf("HTTP status: %s\n", resp.Status)
		}
		panic(fmt.Errorf("dial failed: %w", err))
	}
	defer ws.Close()
	c.ws = ws
	fmt.Println("WebSocket连接已建立")

	if err := c.startSession(); err != nil {
		panic(err)
	}

	for {
		_, raw, err := ws.ReadMessage()
		if err != nil {
			if _, ok := err.(*websocket.CloseError); ok {
				fmt.Println("WebSocket连接已关闭")
			} else {
				fmt.Printf("WebSocket读取错误: %v\n", err)
			}
			return
		}
		c.handleMessage(raw)

		select {
		case <-c.done:
			return
		default:
		}
	}
}
