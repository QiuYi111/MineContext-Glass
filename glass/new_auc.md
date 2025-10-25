# 火山极速识别（AUC Turbo）接入说明

本接口用于 MineContext Glass 在本地算力不足或 WhisperX 推理耗时过长时的云端替代方案。整体目标是保持 `AlignmentManifest → AlignmentSegment` 的数据契约不变，只替换语音识别的实现，从而不破坏现有管线。

## 1. 使用限制与前置条件

- **音频长度**：≤2 小时；更长文件请切回录音文件标准版或本地 WhisperX。
- **文件大小**：≤100 MB，推荐 ≤20 MB（受出口带宽影响）。
- **格式**：PCM / WAV / MP3 / OGG OPUS。建议 ffmpeg 统一导出 16 kHz、单声道 WAV 以减小体积。
- **多声道**：解码耗时随声道数上升，若无法转单声道需预估延迟。
- **资源权限**：账号需开通 `volc.bigasr.auc_turbo`。
- **网络可用性**：依赖公网访问 `openspeech.bytedance.com`。

## 2. 架构整合策略

1. 将现有 `WhisperXRunner` 抽象为通用 `SpeechToTextRunner` 协议，`LocalVideoManager` 仅依赖该协议，避免散落的 if/else。
2. 新增 `AUCTurboRunner`：
   - 读取 `FFmpegRunner` 导出的音频文件；
   - 检查时长/体积，超限时抛出自定义异常交由 VideoManager 回退；
   - 将音频内容做 base64 并一次性 POST 至火山 API；
   - 解析 `utterances[*]` 为 `AlignmentSegment(type=AUDIO)`，维持 `TranscriptionResult` 结构。
3. 失败/超时按现有异常路径处理，`LocalVideoManager` 会写入 `status=failed`，不增加额外状态机。

## 3. 配置项（需写入 `config/config.example` 并使用环境变量注入）

```yaml
glass:
  speech_to_text:
    provider: whisperx  # whisperx | auc_turbo
    auc_turbo:
      base_url: https://openspeech.bytedance.com/api/v3
      resource_id: volc.bigasr.auc_turbo
      app_key: "${AUC_APP_KEY:}"
      access_key: "${AUC_ACCESS_KEY:}"
      request_timeout: 120
      max_file_size_mb: 100
      max_duration_sec: 7200
```

未配置密钥或 provider 仍为 `whisperx` 时继续走本地模型，保证 “never break userspace”。

## 4. 请求规范

- **HTTP 方法**：`POST https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash`
- **Header**

| Header                | 说明                           | 示例                      |
| --------------------- | ------------------------------ | ------------------------- |
| `X-Api-App-Key`     | 火山引擎控制台获取的 AppID     | `123456789`             |
| `X-Api-Access-Key`  | 火山引擎控制台 Access Token    | `your-access-key`       |
| `X-Api-Resource-Id` | 固定 `volc.bigasr.auc_turbo` | `volc.bigasr.auc_turbo` |
| `X-Api-Request-Id`  | UUID，便于排障                 | `67ee89ba-7050-...`     |
| `X-Api-Sequence`    | 固定 `-1`                    | `-1`                    |

- **Body**

```json
{
  "user": { "uid": "你的AppID" },
  "audio": {
    "data": "base64-encoded audio"
    // 或者 "url": "https://example.com/audio.wav"
  },
  "request": { "model_name": "bigmodel" }
}
```

`audio.data` 与 `audio.url` 二选一；若传 URL，请确保上传文件对火山服务可访问。

## 5. 响应示例与映射

成功时响应头包含：

- `X-Api-Status-Code: 20000000`
- `X-Api-Message: OK`
- `X-Tt-Logid: <trace id>`

响应体示例：

```json
{
  "audio_info": { "duration": 2499 },
  "result": {
    "text": "关闭透传。",
    "additions": { "duration": "2499" },
    "utterances": [
      {
        "start_time": 450,
        "end_time": 1530,
        "text": "关闭透传。",
        "words": [
          { "start_time": 450, "end_time": 770, "text": "关", "confidence": 0 },
          { "start_time": 770, "end_time": 970, "text": "闭", "confidence": 0 }
        ]
      }
    ]
  }
}
```

映射规则：

| 火山字段                     | Glass 字段                                   |
| ---------------------------- | -------------------------------------------- |
| `utterances[*].start_time` | `AlignmentSegment.start`（秒）             |
| `utterances[*].end_time`   | `AlignmentSegment.end`（秒）               |
| `utterances[*].text`       | `AlignmentSegment.payload`                 |
| `words`                    | 当前阶段可丢弃，或在 `raw_response` 中保留 |
| `audio_info.duration`      | 可写入 `raw_response`，供调试/监控使用     |

若 `utterances` 为空需要视为异常，抛出 `ValueError` 以保持与 WhisperX runner 行为一致。

## 6. 错误与回退策略

1. **超时/网络失败**：HTTP 非 200、超时、`X-Api-Status-Code ≠ 20000000` 直接抛异常，由 `LocalVideoManager` 写入 FAILED 状态；上层可重试或切换 provider。
2. **配额/鉴权错误**：捕获 4xx/5xx，记录 `X-Tt-Logid`，提醒用户检查密钥或额度。
3. **文件过大/过长**：在上传前就校验 `max_file_size_mb` 与 `max_duration_sec`，必要时自动改用 WhisperX。保持单一代码路径，别额外搞状态文件。

## 7. 实用提示

- 上传 base64 会膨胀 ~33%，所以 20 MB 实际约等价 15 MB 原始文件，ffmpeg 需把采样率、声道控制好。
- `request_timeout` 需要覆盖大段音频（建议 ≥120s），但也要设置合理的连接超时，防止线程池被卡死。
- 建议在日志中打印 `timeline_id` + `X-Tt-Logid`，方便与火山侧对齐排障。

照此接入，可以在 GPU 不可用时默认走云端，同时保留本地路径作为后备，满足 “Never break userspace”。

错误码

错误码

含义

说明

20000000

成功

20000003

静音音频

45000001

请求参数无效

请求参数缺失必需字段 / 字段值无效

45000002

空音频

45000151

音频格式不正确

550XXXX

服务内部处理错误

55000031

服务器繁忙

服务过载，无法处理当前请求。

# Demo

```python
import json
import time
import uuid
import requests
import base64

# 辅助函数：下载文件
def download_file(file_url):
    response = requests.get(file_url)
    if response.status_code == 200:
        return response.content  # 返回文件内容（二进制）
    else:
        raise Exception(f"下载失败，HTTP状态码: {response.status_code}")

# 辅助函数：将本地文件转换为Base64
def file_to_base64(file_path):
    with open(file_path, 'rb') as file:
        file_data = file.read()  # 读取文件内容
        base64_data = base64.b64encode(file_data).decode('utf-8')  # Base64 编码
    return base64_data

# recognize_task 函数
def recognize_task(file_url=None, file_path=None):
    recognize_url = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash"
    # 填入控制台获取的app id和access token
    appid = "{你的appid}"
    token = "{你的access token}"
  
    headers = {
        "X-Api-App-Key": appid,
        "X-Api-Access-Key": token,
        "X-Api-Resource-Id": "volc.bigasr.auc_turbo", 
        "X-Api-Request-Id": str(uuid.uuid4()),
        "X-Api-Sequence": "-1", 
    }

    # 检查是使用文件URL还是直接上传数据
    audio_data = None
    if file_url:
        audio_data = {"url": file_url}
    elif file_path:
        base64_data = file_to_base64(file_path)  # 转换文件为 Base64
        audio_data = {"data": base64_data}  # 使用Base64编码后的数据

    if not audio_data:
        raise ValueError("必须提供 file_url 或 file_path 其中之一")

    request = {
        "user": {
            "uid": appid
        },
        "audio": audio_data,
        "request": {
            "model_name": "bigmodel",
            # "enable_itn": True,
            # "enable_punc": True,
            # "enable_ddc": True,
            # "enable_speaker_info": False,

        },
    }

    response = requests.post(recognize_url, json=request, headers=headers)
    if 'X-Api-Status-Code' in response.headers:
        print(f'recognize task response header X-Api-Status-Code: {response.headers["X-Api-Status-Code"]}')
        print(f'recognize task response header X-Api-Message: {response.headers["X-Api-Message"]}')
        print(time.asctime() + " recognize task response header X-Tt-Logid: {}".format(response.headers["X-Tt-Logid"]))
        print(f'recognize task response content is: {response.json()}\n')
    else:
        print(f'recognize task failed and the response headers are:: {response.headers}\n')
        exit(1)
    return response

# recognizeMode 不变
def recognizeMode(file_url=None, file_path=None):
    start_time = time.time()
    print(time.asctime() + " START!")
    recognize_response = recognize_task(file_url=file_url, file_path=file_path)
    code = recognize_response.headers['X-Api-Status-Code']
    logid = recognize_response.headers['X-Tt-Logid']
    if code == '20000000':  # task finished
        f = open("result.json", mode='w', encoding='utf-8')
        f.write(json.dumps(recognize_response.json(), indent=4, ensure_ascii=False))
        f.close()
        print(time.asctime() + " SUCCESS! \n")
        print(f"程序运行耗时: {time.time() - start_time:.6f} 秒")
    elif code != '20000001' and code != '20000002':  # task failed
        print(time.asctime() + " FAILED! code: {}, logid: {}".format(code, logid))
        print("headers:")
        # print(query_response.content)

def main(): 
    # 示例：通过 URL 或 文件路径选择传入参数
    file_url = "https://example.mp3"
    file_path = "audio/example.mp3"  # 如果你有本地文件，可以选择这个 
    recognizeMode(file_url=file_url)  # 或者 recognizeMode(file_path=file_path)
    # recognizeMode(file_path=file_path)  # 或者 recognizeMode(file_path=file_path)
 
if __name__ == '__main__': 
    main()
```
