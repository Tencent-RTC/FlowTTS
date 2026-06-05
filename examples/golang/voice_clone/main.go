package main

import (
	"encoding/base64"
	"fmt"
	"os"
	"path/filepath"

	"flowtts-golang-examples/flowttsutil"

	"github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/common"
	trtc "github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/trtc/v20190722"
)

const (
	model          = ""
	voiceName      = "MyClonedVoiceGo"
	promptText     = ""
	promptLanguage = ""
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

	audioFile := flowttsutil.ProjectPath(cfg, "test_data", "clone_sample.wav")
	voiceID, err := voiceClone(client, cfg.SdkAppID, audioFile)
	if err != nil {
		panic(err)
	}

	fmt.Println("Voice cloned successfully!")
	fmt.Printf("Voice ID: %s\n", voiceID)
}

func voiceClone(client *trtc.Client, sdkAppID uint64, audioFile string) (string, error) {
	audioData, err := os.ReadFile(audioFile)
	if err != nil {
		return "", err
	}
	audioBase64 := base64.StdEncoding.EncodeToString(audioData)

	req := trtc.NewVoiceCloneRequest()
	req.Model = common.StringPtr(model)
	req.SdkAppId = common.Uint64Ptr(sdkAppID)
	req.VoiceName = common.StringPtr(voiceName)
	req.PromptAudio = common.StringPtr(audioBase64)
	if promptText != "" {
		req.PromptText = common.StringPtr(promptText)
	}
	if promptLanguage != "" {
		req.Language = common.StringPtr(promptLanguage)
	}

	fmt.Printf("Cloning voice: %s\n", voiceName)
	fmt.Printf("Audio: %s\n", filepath.Clean(audioFile))

	resp, err := client.VoiceClone(req)
	if err != nil {
		return "", err
	}
	if resp.Response == nil || resp.Response.VoiceId == nil {
		return "", fmt.Errorf("voice clone response has no VoiceId")
	}

	if resp.Response.RequestId != nil {
		fmt.Printf("RequestId: %s\n", *resp.Response.RequestId)
	}
	return *resp.Response.VoiceId, nil
}
