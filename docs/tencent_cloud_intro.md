# 腾讯云（实时音视频）对话式 TTS 接入

腾讯云对话式 TTS 是基于 TRTC（实时音视频）打造的新一代低延迟语音合成能力，主打**实时对话场景**：超低延迟、拟人度高、支持声音克隆与多语种，能让 AI "听起来像真人"。访问更多实时音视频服务可前往 [TRTC 产品页](https://cloud.tencent.com/product/trtc)。

---

## 一、体验入口

- **全部音色体验页**（输入文本即可在线合成）：<https://web.realtime-ai.chat/app/tts.html>
- **精品音色 ID 清单**（持续更新，含试听文件）：[flow_02_turbo 精品音色列表](https://doc.weixin.qq.com/smartsheet/s3_AS8AdAZRAHECNorj3TwZ8REagnFMY?scode=AJEAIQdfAAolPNM7ckAS8AdAZRAHE&tab=q979lj&viewId=vukaF8)

---

## 二、开通说明

对话式 TTS 依托 **TRTC AI 实时对话方案** 使用，接入前需要先开通 TRTC AI 服务。

**相关计费说明**

- 国内站：<https://cloud.tencent.com/document/product/647/111976>
- 国际站：<https://trtc.io/document/67832?product=pricing>

### 1. 新用户开通（2025 年 11 月 20 日之后）

**国内站**

- 可先领取 **TRTC 包月体验版**，解锁 7 + 7 天的后付费体验权限
- 长期稳定使用建议根据业务情况购买对应的 TRTC 套餐包，详见[国内站计费文档](https://cloud.tencent.com/document/product/647/111976)

**国际站**

- 需要先购买 **RTC Engine 轻量版或以上套餐包** 解锁 TTS 后付费权限
- 详见[国际站计费文档](https://trtc.io/document/67832?product=pricing)

### 2. TTS 权限长期使用条件

| 站点 | 包含 TTS 的套餐 |
|------|----------------|
| 国内站 | AI 智能识别包 · 轻量版 / AI 智能识别包 · 尊享版 / TRTC 包月套餐期间的旗舰版 Plus 能力 |
| 国际站 | RTC Engine 轻量版及以上 |

> **快速理解**：国内只要拥有 AI 智能识别包（轻量/尊享）或开通 TRTC 包月旗舰 Plus 套餐，即可解锁国内对话式 TTS 能力，包内赠送的 AI 时长可用于抵扣相关 AI 服务用量；国际购买任意 RTC Engine 轻量级或更高套餐包即可开启后付费。

> **折扣优惠**：如需了解相关折扣政策，请联系您的商务经理和架构师评估。

---

## 三、TTS 模型与音色说明

### 模型：flow_02_turbo（推荐）

- **定位**：对话场景主推 TTS 模型
- **特点**：
  - **超低延迟**：首包低至 300ms，适合实时对话、实时配音
  - **拟人度强**：音质高、自然度高，具备口语化表达
  - **多语言支持**：中文、英文、日语、韩语、粤语、马来语、印尼语、泰语、越南语、阿拉伯语共 10 种
- **音色列表**：[精品音色清单](https://doc.weixin.qq.com/smartsheet/s3_AS8AdAZRAHECNorj3TwZ8REagnFMY?scode=AJEAIQdfAAolPNM7ckAS8AdAZRAHE&tab=q979lj&viewId=vukaF8)

> 更多语种需求请联系技术团队评估。

---

## 四、集成至 TRTC AI 对话方案

在 TRTC AI 对话配置中加入 TRTC 的 TTS 服务配置，即可完成对话式语音回复的打通。

> 如果您**不通过 TRTC AI 对话方案**直接使用 TTS，请跳转至[第五章 API 接入说明](#五api-接入说明)。

### AI 实时对话计费说明

- **国内站**：使用 AI 对话服务会产生 AI 实时对话服务费、语音转文本和语音合成费用（选择第三方服务则不产生对应费用）。详见 [AI 对话计费](https://cloud.tencent.com/document/product/647/115755) 与 [TRTC 计费说明](https://cloud.tencent.com/document/product/647/111976)
- **国际站**：参考 [国际站 AI 对话计费](https://trtc.io/document/67833?product=pricing) 与 [国际站 TRTC 计费](https://trtc.io/document/67832?product=pricing)
- AI 对话通道、ASR 与 TTS 默认 **100 路并发**，需要提升请联系商务与产研

### 跑通 AI 实时对话并配置 TTS

| 站点 | 跑通 AI 实时对话 | 配置 TRTC TTS |
|------|------------------|---------------|
| 国内站 | [快速跑通](https://cloud.tencent.com/document/product/647/115412) | [配置文档](https://cloud.tencent.com/document/product/647/115414) |
| 国际站 | [Quickstart](https://trtc.io/document/68337?product=conversationalai) | [Configuration](https://trtc.io/document/68340?product=conversationalai) |

### 配置示例

```json
{
  "TTSType": "flow",          // 【必填】固定填 "flow"
  "VoiceId": "xxxx",          // 【必填】精品音色 ID 或克隆音色 ID
  "Model": "flow_02_turbo",   // 【可选】TTS 模型，默认 flow_02_turbo
  "Speed": 1.0,               // 【可选】语速，范围 [0.5, 2.0]，默认 1.0
  "Volume": 1.0,              // 【可选】音量，范围 (0, 10]，默认 1.0
  "Pitch": 0,                 // 【可选】音高，范围 [-12, 12]，默认 0
  "Language": "zh"            // 【可选】语言（ISO 639-1），共支持 10 种，详见下方语言代码表
}
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `TTSType` | 是 | 固定为 `"flow"`，表示使用对话式 TTS 能力 |
| `VoiceId` | 是 | 官方提供的**精品音色 ID** 或通过**声音克隆**生成的专属 `VoiceId` |
| `Model` | 否 | 默认 `flow_02_turbo` |
| `Speed` / `Volume` / `Pitch` | 否 | 微调语速、音量、音高，便于按业务场景做个性化设置 |
| `Language` | **强烈推荐** | 遵循 ISO 639-1，目前共支持 10 种语言（见下表）；正确填写有助于模型处理发音与停顿 |

### 支持的语言代码（ISO 639-1）

目前共支持以下 **10 种语言**：

| 语言 | 代码 |
|------|------|
| 中文 | `zh` |
| 英文 | `en` |
| 日语 | `ja` |
| 韩语 | `ko` |
| 粤语 | `yue` |
| 马来语 | `ms` |
| 阿拉伯语 | `ar` |
| 印尼语 | `id` |
| 泰语 | `th` |
| 越南语 | `vi` |

---

## 五、API 接入说明

如果您不通过 TRTC AI 对话方案接入，可以根据场景选择以下任一 API。

### 接口选择建议

| 场景 | 推荐接口 | 原因 |
|------|----------|------|
| 实时对话、Agent 语音输出 | **WebSocket 双向流式** | LLM token 流式产出后即时推给 TTS，首句最快出声，可中途打断 |
| 已知完整文本，要求最低首包延迟 | **SSE 流式 TTS** | 一次请求边收边播，比非流式延迟低 50-100 ms |
| 离线播报、批量生成、文件导出 | **非流式 TTS** | 拿到完整音频文件（pcm/wav/mp3），方便后处理 |
| 需要专属音色 | **声音克隆** | 提交样本得到 `VoiceId`，再配合上述任意接口使用 |

### 1. 声音克隆（音色快速复刻）

- **功能**：提交少量语音样本即可创建专属克隆音色，生成的 `VoiceId` 与精品音色 ID 用法一致，可在对话式 TTS 中直接使用
- **文档**：<https://cloud.tencent.com/document/product/647/122473>（对此文档有问题请直接联系技术团队，无需走工单）

> **注意**
> - 声音克隆服务目前处于内测阶段
> - 用于合成特定音色时，您授权腾讯云使用您提供或上传的音频、人声信息等数据用于合成语音复刻；可随时请求删除已上传内容，删除后不会留存
> - 更多使用须知见[第六章 相关服务协议告知](#六相关服务协议告知)

### 2. SSE 流式文本转语音 API

- **功能**：通过 Server-Sent Events (SSE) 进行流式 TTS，在对话场景下可边生成边播放，大幅降低首包延迟
- **文档**：<https://cloud.tencent.com/document/product/647/122474>（对此文档有问题请直接联系技术团队，无需走工单）

> 默认 **QPS 限制 20**，需要提升请联系技术团队。

### 3. 文本转语音 API（非流式）

- **功能**：非流式 TTS，适合对延迟不敏感的离线/异步生成场景
- **文档**：<https://cloud.tencent.com/document/api/647/122475>（对此文档有问题请直接联系技术团队，无需走工单）

> 默认 **QPS 限制 20**，需要提升请联系技术团队。

### 4. WebSocket 双向流式 API

- **功能**：边发文本边收音频，专为 LLM 流式输出对接设计；服务端自动分句，每句合成完成立即返回；支持立即打断
- **文档**：[WebSocket 双向流式协议](https://github.com/Tencent-RTC/FlowTTS/blob/main/docs/ws_bidirection_protocol.md)（含鉴权、消息格式、事件、错误码与完整示例）

### 5. 完整示例代码

仓库中提供 Python / Node.js 双语言、覆盖以上四种接口的完整示例，建议直接基于示例进行二次集成：

> **官方示例仓库**：<https://github.com/Tencent-RTC/FlowTTS>

---

## 六、相关服务协议告知

1. 上述 TTS 服务全部基于 TRTC 能力，开通过程会创建 TRTC SDKAppId，相关隐私保护与合规受以下条款约束，使用相关服务即代表您同意相关规定：
   - <https://cloud.tencent.com/document/product/647/57574>
   - <https://cloud.tencent.com/document/product/647/97575>
   - <https://cloud.tencent.com/document/product/301/1967#20f4b8e9-fea7-4761-84c4-9de01db6c807>
2. 使用语音合成（TTS）和声音快速复刻（克隆）功能时，您需要确保：
   - **输入素材合法合规**，不含有任何违反法律法规之内容，不应输入未经授权的自然人个人信息、未经授权的知识产权数据、商业秘密数据等
   - **拥有合法授权**：输入素材为您自行所有或已获取对应权利人充分、必要且有效的合法许可及授权，不侵犯任何第三方合法权益（包括但不限于知识产权、肖像权、名誉权、隐私权、商业秘密等）；否则因此产生的违约、侵权纠纷或法律责任由您自行处理与承担

---

## 七、使用小结

1. **开通**：先开通 TRTC 与对应 TTS 权限（见[第二章](#二开通说明)）
2. **选音色**：在[音色清单](https://doc.weixin.qq.com/smartsheet/s3_AS8AdAZRAHECNorj3TwZ8REagnFMY?scode=AJEAIQdfAAolPNM7ckAS8AdAZRAHE&tab=q979lj&viewId=vukaF8)中选择音色 ID，或通过声音克隆生成专属 `VoiceId`
3. **配置**：按照[配置示例](#配置示例)将 TTS 能力接入 TRTC AI 对话方案，或参考[第五章 API 接入](#五api-接入说明)直接调用
4. **验证**：访问[体验页](https://web.realtime-ai.chat/app/tts.html)快速验证效果
