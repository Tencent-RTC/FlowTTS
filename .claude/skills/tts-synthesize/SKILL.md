---
name: tts-synthesize
description: 使用 FlowTTS 将文本合成为语音音频。支持选择音色、调节语速、多语言合成。当用户想将文本转为语音、生成音频时使用。
allowed-tools: Read, Bash, Glob, Write
argument-hint: [文本内容或文件路径] [--voice 音色ID] [--speed 语速] [--language 语言] [--output 输出路径]
---

## 角色定义

你是 FlowTTS 语音合成助手，帮助用户将文本转换为高质量语音音频。

## 前置条件

语音合成需要以下环境配置：
- Python 3.8+
- 已安装依赖：`pip install python-dotenv tencentcloud-sdk-python`
- 项目根目录 `.env` 文件中配置了以下环境变量：
  - `TENCENTCLOUD_SECRET_ID`
  - `TENCENTCLOUD_SECRET_KEY`
  - `TENCENTCLOUD_SDK_APP_ID`（可选，有默认值）

## 输入处理

从 `$ARGUMENTS` 中解析以下参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 文本/文件路径 | 要合成的文本，或 `.podcast.json` 文件路径 | 必填 |
| `--voice` | 音色 VoiceId | `v-female-R2s4N9qJ`（温柔姐姐） |
| `--speed` | 语速，范围 0.5-2.0 | `1.0` |
| `--volume` | 音量，范围 0.01-10 | `1.0` |
| `--pitch` | 音高，范围 -12 到 12 | `0` |
| `--language` | 语言：zh/en/yue/ja/ko/ar/id/th | `zh` |
| `--output` / `-o` | 输出文件路径 | `output.wav` |
| `--sample-rate` | 采样率：16000 或 24000 | `24000` |

### 识别规则

- 如果参数是以 `.podcast.json` 结尾的文件路径 → 播客合成模式
- 如果参数是其他文件路径（含 `/` 或 `.txt` 等） → 读取文件内容作为合成文本
- 其余情况 → 直接作为合成文本

## 工作流程

### 模式一：单文本合成

适用于合成单段文本。

#### 1. 检查环境

```bash
test -f .env && grep -c "TENCENTCLOUD_SECRET_ID" .env
```

#### 2. 如果用户未指定音色

推荐用户先使用 `/tts-voices` 选择合适的音色。或使用默认音色直接合成。

#### 3. 执行合成

使用 Bash 工具运行以下 Python 脚本：

```bash
cd {project_root} && python -c "
import os, io, json, wave, base64
from dotenv import load_dotenv
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.trtc.v20190722 import trtc_client, models

load_dotenv()
cred = credential.Credential(os.getenv('TENCENTCLOUD_SECRET_ID'), os.getenv('TENCENTCLOUD_SECRET_KEY'))
http_profile = HttpProfile()
http_profile.endpoint = 'trtc.ai.tencentcloudapi.com'
http_profile.reqTimeout = 120
http_profile.keepAlive = True
http_profile.pre_conn_pool_size = 3
client_profile = ClientProfile()
client_profile.httpProfile = http_profile
client = trtc_client.TrtcClient(cred, 'ap-beijing', client_profile)

req = models.TextToSpeechSSERequest()
req.from_json_string(json.dumps({
    'Model': '',
    'Text': '''{text}''',
    'Voice': {
        'VoiceId': '{voice_id}',
        'Speed': {speed},
        'Volume': {volume},
        'Pitch': {pitch},
        'Language': '{language}'
    },
    'AudioFormat': {'Format': 'pcm', 'SampleRate': {sample_rate}},
    'SdkAppId': int(os.getenv('TENCENTCLOUD_SDK_APP_ID', '1400000000'))
}))

resp = client.TextToSpeechSSE(req)
chunks = []
for event in resp:
    if isinstance(event, dict) and 'data' in event:
        try:
            data = json.loads(event['data'].strip())
            if data.get('Type') == 'audio' and data.get('Audio'):
                chunks.append(base64.b64decode(data['Audio']))
            if data.get('IsEnd'): break
        except: continue

if chunks:
    pcm = b''.join(chunks)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate({sample_rate})
        w.writeframes(pcm)
    with open('{output}', 'wb') as f:
        f.write(buf.getvalue())
    dur = len(pcm) / ({sample_rate} * 2)
    print(f'合成成功! 音频时长: {dur:.1f}s, 文件: {output}')
else:
    print('未收到音频数据')
"
```

#### 4. 输出结果

```
语音合成完成!

- 输出文件: {output}
- 音频时长: {duration}s
- 音色: {voice_id}（{voice_name}）
- 语速: {speed} | 语言: {language}
```

### 模式二：播客合成

当输入为 `.podcast.json` 文件时，调用已有的播客合成脚本。

#### 1. 验证播客脚本

读取 JSON 文件，确认包含 `dialogue` 数组。

#### 2. 选择音色

如果用户未指定音色，从 `voices/voices.json` 中推荐适合播客的一男一女音色组合。

#### 3. 执行合成

```bash
cd {project_root} && python .claude/skills/podcast-generate/scripts/synthesize_podcast.py \
  -i {podcast_json_path} \
  -o {output_path} \
  --voice-a {voice_a_id} \
  --voice-b {voice_b_id} \
  --sample-rate {sample_rate}
```

#### 4. 输出结果

```
播客音频合成完成!

- 输出文件: {output}
- 对话轮次: {total_turns}
- Speaker A: {voice_a_name}（{voice_a_id}）
- Speaker B: {voice_b_name}（{voice_b_id}）
```

## 注意事项

- 单次合成文本不宜过长，建议单段不超过 500 字
- 流式 SSE API 仅支持 pcm 格式输出，脚本会自动转为 wav
- 如需 mp3 格式，可使用 ffmpeg 转换：`ffmpeg -i output.wav output.mp3`
- 合成速度受文本长度和网络状况影响

## 错误处理

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| `AuthFailure` | 密钥配置错误 | 检查 `.env` 中的 SECRET_ID 和 SECRET_KEY |
| `InvalidParameter.VoiceId` | 音色 ID 无效 | 使用 `/tts-voices` 查看可用音色 |
| 无音频数据返回 | 文本为空或网络问题 | 检查文本内容，重试 |
| 超时 | 文本过长或网络慢 | 缩短文本，分段合成 |
