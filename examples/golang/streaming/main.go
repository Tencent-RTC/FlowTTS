package main

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"flowtts-golang-examples/flowttsutil"

	"github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/common"
	tchttp "github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/common/http"
	trtc "github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/trtc/v20190722"
)

const (
	model      = ""
	voiceID    = "v-female-R2s4N9qJ"
	language   = "zh"
	sampleRate = 24000
	testText   = "欢迎使用腾讯云FlowTTS，这是Go流式SSE合成示例。"
)

type ssePayload struct {
	Type      string `json:"Type"`
	Audio     string `json:"Audio"`
	IsEnd     bool   `json:"IsEnd"`
	RequestID string `json:"RequestId"`
}

func main() {
	// TTS audio chunks are base64-encoded in SSE data lines and can exceed
	// bufio.Scanner's default 64 KiB token limit used by the Tencent Cloud SDK.
	tchttp.SSEScannerBufferMaxBytes = 16 * 1024 * 1024

	cfg, err := flowttsutil.LoadConfig()
	if err != nil {
		panic(err)
	}

	client, err := flowttsutil.NewClient(cfg, "trtc.ai.tencentcloudapi.com")
	if err != nil {
		panic(err)
	}

	if _, err := textToSpeechSSE(client, cfg.SdkAppID, testText); err != nil {
		panic(err)
	}
}

func textToSpeechSSE(client *trtc.Client, sdkAppID uint64, text string) (string, error) {
	req := trtc.NewTextToSpeechSSERequest()
	req.Model = common.StringPtr(model)
	req.Text = common.StringPtr(text)
	req.SdkAppId = common.Uint64Ptr(sdkAppID)
	req.Voice = &trtc.Voice{
		VoiceId: common.StringPtr(voiceID),
		Speed:   common.Float64Ptr(1.0),
		Volume:  common.Float64Ptr(1.0),
		Pitch:   common.Int64Ptr(0),
	}
	req.Language = common.StringPtr(language)
	req.AudioFormat = &trtc.AudioFormat{
		Format:     common.StringPtr("pcm"),
		SampleRate: common.Uint64Ptr(sampleRate),
	}

	fmt.Printf("Starting streaming SSE TTS\n")
	fmt.Printf("Voice: %s\n", voiceID)
	fmt.Printf("Text: %s\n", text)

	start := time.Now()
	resp, err := client.TextToSpeechSSE(req)
	if err != nil {
		return "", err
	}

	var pcm []byte
	eventCount := 0
	audioChunks := 0
	var firstAudioLatency time.Duration

	for event := range resp.Events {
		eventCount++
		if event.Err != nil {
			return "", event.Err
		}
		if len(event.Data) == 0 {
			continue
		}

		var payload ssePayload
		if err := json.Unmarshal(event.Data, &payload); err != nil {
			continue
		}
		if payload.Type == "audio" && payload.Audio != "" {
			if audioChunks == 0 {
				firstAudioLatency = time.Since(start)
			}
			chunk, err := base64.StdEncoding.DecodeString(payload.Audio)
			if err != nil {
				return "", err
			}
			pcm = append(pcm, chunk...)
			audioChunks++
		}
		if payload.IsEnd {
			break
		}
	}

	if len(pcm) == 0 {
		return "", fmt.Errorf("TextToSpeechSSE response has no audio")
	}

	wav := flowttsutil.PCMToWAV(pcm, sampleRate, 1, 16)
	outputDir, err := os.Getwd()
	if err != nil {
		return "", err
	}
	outputPath := filepath.Join(outputDir, fmt.Sprintf("tts_%s_streaming_%d.wav", voiceID, time.Now().Unix()))
	if err := os.WriteFile(outputPath, wav, 0644); err != nil {
		return "", err
	}

	if resp.Response != nil && resp.Response.RequestId != nil {
		fmt.Printf("RequestId: %s\n", *resp.Response.RequestId)
	}
	fmt.Printf("Events: %d\n", eventCount)
	fmt.Printf("Audio chunks: %d\n", audioChunks)
	fmt.Printf("PCM bytes: %d\n", len(pcm))
	fmt.Printf("WAV bytes: %d\n", len(wav))
	fmt.Printf("First audio latency: %.0fms\n", float64(firstAudioLatency.Milliseconds()))
	fmt.Printf("Total elapsed: %.0fms\n", float64(time.Since(start).Milliseconds()))
	fmt.Printf("Audio saved to: %s\n", outputPath)
	return outputPath, nil
}
