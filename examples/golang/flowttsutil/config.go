package flowttsutil

import (
	"encoding/binary"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strconv"

	"github.com/joho/godotenv"
	"github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/common"
	"github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/common/profile"
	trtc "github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/trtc/v20190722"
)

const Region = "ap-beijing"

type Config struct {
	SecretID  string
	SecretKey string
	SdkAppID  uint64
	Root      string
}

func LoadConfig() (*Config, error) {
	root, err := findProjectRoot()
	if err != nil {
		return nil, err
	}
	_ = godotenv.Load(filepath.Join(root, ".env"))

	secretID := os.Getenv("TENCENTCLOUD_SECRET_ID")
	secretKey := os.Getenv("TENCENTCLOUD_SECRET_KEY")
	if secretID == "" || secretKey == "" {
		return nil, errors.New("TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY are required")
	}

	sdkAppIDText := firstNonEmpty(os.Getenv("TENCENTCLOUD_SDK_APP_ID"), os.Getenv("SDKAPPID"), "1400000000")
	sdkAppID, err := strconv.ParseUint(sdkAppIDText, 10, 64)
	if err != nil {
		return nil, fmt.Errorf("invalid SDK App ID %q: %w", sdkAppIDText, err)
	}

	return &Config{
		SecretID:  secretID,
		SecretKey: secretKey,
		SdkAppID:  sdkAppID,
		Root:      root,
	}, nil
}

func NewClient(cfg *Config, endpoint string) (*trtc.Client, error) {
	cred := common.NewCredential(cfg.SecretID, cfg.SecretKey)

	httpProfile := profile.NewHttpProfile()
	httpProfile.Endpoint = endpoint
	httpProfile.ReqTimeout = 120

	clientProfile := profile.NewClientProfile()
	clientProfile.HttpProfile = httpProfile

	return trtc.NewClient(cred, Region, clientProfile)
}

func ProjectPath(cfg *Config, parts ...string) string {
	all := append([]string{cfg.Root}, parts...)
	return filepath.Join(all...)
}

func PCMToWAV(pcm []byte, sampleRate uint32, channels uint16, bitsPerSample uint16) []byte {
	byteRate := sampleRate * uint32(channels) * uint32(bitsPerSample) / 8
	blockAlign := channels * bitsPerSample / 8
	dataSize := uint32(len(pcm))

	wav := make([]byte, 44+len(pcm))
	copy(wav[0:4], []byte("RIFF"))
	binary.LittleEndian.PutUint32(wav[4:8], dataSize+36)
	copy(wav[8:12], []byte("WAVE"))
	copy(wav[12:16], []byte("fmt "))
	binary.LittleEndian.PutUint32(wav[16:20], 16)
	binary.LittleEndian.PutUint16(wav[20:22], 1)
	binary.LittleEndian.PutUint16(wav[22:24], channels)
	binary.LittleEndian.PutUint32(wav[24:28], sampleRate)
	binary.LittleEndian.PutUint32(wav[28:32], byteRate)
	binary.LittleEndian.PutUint16(wav[32:34], blockAlign)
	binary.LittleEndian.PutUint16(wav[34:36], bitsPerSample)
	copy(wav[36:40], []byte("data"))
	binary.LittleEndian.PutUint32(wav[40:44], dataSize)
	copy(wav[44:], pcm)
	return wav
}

func firstNonEmpty(values ...string) string {
	for _, value := range values {
		if value != "" {
			return value
		}
	}
	return ""
}

func findProjectRoot() (string, error) {
	dir, err := os.Getwd()
	if err != nil {
		return "", err
	}

	for {
		if fileExists(filepath.Join(dir, ".env.example")) || fileExists(filepath.Join(dir, ".env")) {
			return dir, nil
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			return "", errors.New("project root not found")
		}
		dir = parent
	}
}

func fileExists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}
