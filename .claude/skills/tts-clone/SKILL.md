---
name: tts-clone
description: 使用 FlowTTS 声音克隆功能，从音频样本创建自定义音色。当用户想克隆声音、创建自定义音色时使用。
allowed-tools: Read, Bash, Glob, Write
argument-hint: [音频文件路径]
---

## 角色定义

你是 FlowTTS 声音克隆助手，帮助用户从音频样本创建自定义音色。

## 前置条件

声音克隆需要以下环境配置：
- Python 3.8+
- 已安装依赖：`pip install python-dotenv tencentcloud-sdk-python`
- 项目根目录 `.env` 文件中配置了以下环境变量：
  - `TENCENTCLOUD_SECRET_ID`
  - `TENCENTCLOUD_SECRET_KEY`
  - `TENCENTCLOUD_SDK_APP_ID`（可选，有默认值）

## 输入处理

- 如果 `$ARGUMENTS` 是一个文件路径，作为音频样本路径
- 如果没有参数，提示用户提供音频文件路径

## 音频要求

克隆音频样本必须满足以下条件：
- **格式**: WAV（16kHz 单声道）
- **时长**: 10-180 秒
- **质量**: 清晰无噪音，单人说话

## 工作流程

### 1. 验证音频文件

检查用户提供的音频文件是否存在，使用 Bash 工具检查文件信息：

```bash
file {audio_path}
```

如果文件不存在或格式不对，给出明确提示。

### 2. 检查环境配置

使用 Bash 工具验证 `.env` 文件存在且包含必要变量：

```bash
test -f .env && grep -c "TENCENTCLOUD_SECRET_ID" .env
```

如果未配置，指导用户：
```
cp .env.example .env
# 然后编辑 .env 文件填入腾讯云密钥
```

### 3. 执行克隆

调用克隆脚本（复用项目中已有的 example）：

```bash
cd {project_root} && python examples/python/example_voice_clone.py
```

如果用户的音频路径不是默认路径 `test_data/clone_sample.wav`，需要先修改脚本中的 `CLONE_AUDIO_FILE` 变量，或直接使用内联 Python 脚本完成克隆。

推荐使用以下命令直接调用：

```bash
cd {project_root} && python -c "
import os, json, base64
from dotenv import load_dotenv
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.trtc.v20190722 import trtc_client, models

load_dotenv()
cred = credential.Credential(os.getenv('TENCENTCLOUD_SECRET_ID'), os.getenv('TENCENTCLOUD_SECRET_KEY'))
http_profile = HttpProfile()
http_profile.endpoint = 'trtc.tencentcloudapi.com'
http_profile.reqTimeout = 120
client_profile = ClientProfile()
client_profile.httpProfile = http_profile
client = trtc_client.TrtcClient(cred, 'ap-beijing', client_profile)

with open('{audio_path}', 'rb') as f:
    audio_base64 = base64.b64encode(f.read()).decode('utf-8')

req = models.VoiceCloneRequest()
req.from_json_string(json.dumps({
    'Model': '',
    'SdkAppId': int(os.getenv('TENCENTCLOUD_SDK_APP_ID', '1400000000')),
    'VoiceName': '{voice_name}',
    'PromptAudio': audio_base64
}))
resp = client.VoiceClone(req)
print(f'VoiceId: {resp.VoiceId}')
"
```

### 4. 输出结果

克隆成功后，输出：

```
声音克隆成功!

- VoiceId: `{cloned_voice_id}`
- 音色名称: {voice_name}

接下来你可以：
1. 使用此音色合成语音: /tts-synthesize --voice {cloned_voice_id} 你要合成的文本
2. 在播客中使用: 在 synthesize_podcast.py 中指定 --voice-a 或 --voice-b 为此 VoiceId
```

### 5. 错误处理

常见错误及解决方案：

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| `AuthFailure` | 密钥配置错误 | 检查 `.env` 中的 SECRET_ID 和 SECRET_KEY |
| 音频格式错误 | 非 WAV 或采样率不对 | 使用 ffmpeg 转换：`ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav` |
| 音频时长不符 | 不在 10-180 秒范围 | 裁剪音频到合适时长 |
