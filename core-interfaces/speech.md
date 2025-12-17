# Speech Interface

Interface contract for speech-to-text (ASR) and text-to-speech (TTS) services.

## Interface ID
`speech`

## Version
`v1`

## Description
Provides audio transcription (ASR), speech synthesis (TTS), and related audio processing capabilities.

---

## Required Capabilities

### Transcription (ASR)
| Operation | Method | Description |
| :--- | :--- | :--- |
| `transcribe` | `POST /transcribe` | Convert audio to text |
| `transcribe_stream` | `WS /transcribe/stream` | Real-time transcription |

#### Request Format
```json
{
  "audio": "base64_encoded_audio",
  "language": "en",
  "format": "wav"
}
```

#### Response Format
```json
{
  "text": "transcribed text",
  "language": "en",
  "confidence": 0.95,
  "segments": [...]
}
```

### Synthesis (TTS)
| Operation | Method | Description |
| :--- | :--- | :--- |
| `synthesize` | `POST /synthesize` | Convert text to audio |

#### Request Format
```json
{
  "text": "Hello world",
  "voice": "default",
  "format": "wav"
}
```

---

## Health Endpoint
`GET /healthz` or `GET /health`

---

## Implementations
- `whisper-server` - OpenAI Whisper for ASR
