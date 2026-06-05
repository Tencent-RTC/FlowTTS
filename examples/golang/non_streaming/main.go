package main

import (
	"encoding/base64"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"flowtts-golang-examples/flowttsutil"

	"github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/common"
	trtc "github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/trtc/v20190722"
)

const (
	model      = ""
	voiceID    = "v-female-R2s4N9qJ"
	language   = "zh"
	sampleRate = 24000
	testText   = "欢迎使用腾讯云FlowTTS，这是Go非流式合成示例。"
)

func main() {
	cfg, err := flowttsutil.LoadConfig()
	if err != nil {
		panic(err)
	}

	client, err := flowttsutil.NewClient(cfg, "trtc.tencentcloudapi.com")
	if err != nil {
		panic(err)
	}

	if _, err := textToSpeech(client, cfg.SdkAppID, testText, "mp3"); err != nil {
		panic(err)
	}
	if _, err := textToSpeech(client, cfg.SdkAppID, "欢迎使用腾讯云FlowTTS，这是Go非流式PCM转WAV示例。", "pcm"); err != nil {
		panic(err)
	}
}

func textToSpeech(client *trtc.Client, sdkAppID uint64, text string, audioFormat string) (string, error) {
	req := trtc.NewTextToSpeechRequest()
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
		Format:     common.StringPtr(audioFormat),
		SampleRate: common.Uint64Ptr(sampleRate),
	}

	fmt.Printf("\nStarting non-streaming TTS\n")
	fmt.Printf("Voice: %s\n", voiceID)
	fmt.Printf("Text: %s\n", text)
	fmt.Printf("Format: %s\n", audioFormat)

	start := time.Now()
	resp, err := client.TextToSpeech(req)
	if err != nil {
		return "", err
	}
	elapsed := time.Since(start)

	if resp.Response == nil || resp.Response.Audio == nil {
		return "", fmt.Errorf("TextToSpeech response has no audio")
	}
	audioData, err := base64.StdEncoding.DecodeString(*resp.Response.Audio)
	if err != nil {
		return "", err
	}

	outputDir, err := os.Getwd()
	if err != nil {
		return "", err
	}

	var outputData []byte
	ext := audioFormat
	if audioFormat == "pcm" {
		outputData = flowttsutil.PCMToWAV(audioData, sampleRate, 1, 16)
		ext = "wav"
	} else {
		outputData = audioData
	}

	filename := fmt.Sprintf("tts_%s_%d.%s", voiceID, time.Now().Unix(), ext)
	outputPath := filepath.Join(outputDir, filename)
	if err := os.WriteFile(outputPath, outputData, 0644); err != nil {
		return "", err
	}

	if resp.Response.RequestId != nil {
		fmt.Printf("RequestId: %s\n", *resp.Response.RequestId)
	}
	if resp.Response.TotalDurationMs != nil {
		fmt.Printf("TotalDurationMs: %d\n", *resp.Response.TotalDurationMs)
	}
	fmt.Printf("Audio bytes: %d\n", len(outputData))
	fmt.Printf("Time elapsed: %.0fms\n", float64(elapsed.Milliseconds()))
	fmt.Printf("Audio saved to: %s\n", outputPath)
	return outputPath, nil
}
