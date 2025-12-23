# Test Data

Place your audio sample for voice cloning here.

## Audio Requirements

- **File name**: `clone_sample.wav`
- **Format**: WAV, 16kHz, mono
- **Duration**: 10-180 seconds
- **Content**: Clear speech, minimal background noise

## Convert Audio (if needed)

```bash
# Convert to required format
ffmpeg -i your_audio.mp3 -ar 16000 -ac 1 clone_sample.wav
```
