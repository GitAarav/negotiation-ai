# Multilingual Interface Layer

This project implements only the multilingual input/output interface for a dispute resolution platform. The negotiation engine remains external and English-only.

## Architecture

```text
Speech / Text / Document input
    -> Language detection
    -> Translation to English
    -> External negotiation API (English only)
    -> English response
    -> Translation to user preferred language
    -> Text response + optional speech synthesis
```

### Core modules

- `app/services/speech.py`: multilingual speech-to-text using Whisper.
- `app/services/language.py`: text language detection and language code normalization.
- `app/services/translation.py`: translation provider abstraction with an OpenAI-backed implementation.
- `app/services/documents.py`: PDF parsing plus OCR fallback for scanned PDFs and images.
- `app/services/negotiation.py`: black-box external API adapter.
- `app/services/tts.py`: localized speech generation via ElevenLabs.
- `app/services/pipeline.py`: orchestrates end-to-end flow and stores original plus translated data.
- `app/repositories.py`: SQLite persistence for interactions and user preferred languages.

## Features implemented

- Accepts text, speech, and document uploads.
- Converts all incoming content to English before calling the negotiation engine.
- Converts English responses back to each user's preferred language.
- Supports multi-user preferred-language mapping through `user_id`.
- Stores original text, English input, English response, and localized response.
- Returns side-by-side original and translated content.
- Includes structured error handling for unsupported language, translation failure, document failure, speech failure, and negotiation API failure.
- Includes a translation confidence field when a provider returns one.

## Project structure

```text
app/
  config.py
  database.py
  dependencies.py
  errors.py
  main.py
  models.py
  repositories.py
  services/
    documents.py
    language.py
    negotiation.py
    pipeline.py
    speech.py
    translation.py
    tts.py
requirements.txt
.env.example
README.md
```

## API endpoints

### `POST /api/v1/text`

Processes multilingual text input and negotiates through the English-only engine.

```json
{
  "user_id": "user-a",
  "text": "எனக்கு வேலைக்கான பணம் கிடைக்கவில்லை",
  "source_language": "ta",
  "preferred_output_language": "hi",
  "include_audio": true
}
```

### `POST /api/v1/speech`

Multipart form upload.

- `user_id`: string
- `preferred_output_language`: optional language code
- `include_audio`: boolean
- `audio`: uploaded audio file

### `POST /api/v1/documents`

Multipart form upload.

- `user_id`: string
- `preferred_output_language`: optional language code
- `include_audio`: boolean
- `document`: uploaded PDF or image

### `POST /api/v1/translate`

```json
{
  "text": "வணக்கம்",
  "source_language": "ta",
  "target_language": "en"
}
```

### `POST /api/v1/users/{user_id}/preferences`

Stores the output language preference for a given user.

```json
{
  "preferred_language": "hi"
}
```

## Example end-to-end flow

Tamil speech input from User A, with Hindi as the preferred output language:

1. `POST /api/v1/speech` with Tamil audio and `preferred_output_language=hi`.
2. Whisper transcribes speech to Tamil text and detects `ta`.
3. Translation module converts Tamil to English.
4. English text is sent to `POST /negotiation-engine`.
5. English suggestion is returned, for example: `A 70% settlement is reasonable`.
6. Translation module converts that English suggestion to Hindi.
7. ElevenLabs optionally synthesizes Hindi speech.
8. The interaction is stored with original transcript, English handoff text, English response, and Hindi response.

Example negotiation request:

```json
{
  "input": "The freelancer completed the work but has not received payment."
}
```

Example final API response shape:

```json
{
  "interaction_id": 12,
  "user_id": "user-a",
  "channel": "speech",
  "source_language": "ta",
  "target_language": "hi",
  "original_text": "எனக்கு வேலைக்கான பணம் கிடைக்கவில்லை",
  "english_input": "I have not received payment for the completed work.",
  "english_response": "A 70% settlement is reasonable",
  "localized_response_text": "70% समझौता उचित है",
  "localized_response_audio_base64": "<base64-audio>",
  "translation_confidence": null,
  "side_by_side": {
    "original_text": "எனக்கு வேலைக்கான பணம் கிடைக்கவில்லை",
    "english_input": "I have not received payment for the completed work.",
    "english_response": "A 70% settlement is reasonable",
    "localized_response_text": "70% समझौता उचित है"
  }
}
```

## Error handling

- Unsupported language: returns `422` with `unsupported_language`.
- Translation failure: returns `502` with `translation_failed`.
- Speech processing failure: returns `422` with `speech_processing_failed`.
- Document processing failure: returns `422` with `document_processing_failed`.
- Negotiation API failure: returns `502` with `negotiation_api_failed`.
- TTS failure: returns `502` with `tts_failed`.

## Local run instructions

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in:

- `OPENAI_API_KEY` for translation
- `NEGOTIATION_API_URL` for the external English-only engine
- `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID` for speech output
- `TESSERACT_CMD` if Tesseract is not on your `PATH`

4. Start the API:

```bash
uvicorn app.main:app --reload
```

5. Open `http://localhost:8000/docs` for Swagger UI.

## Temporary mock negotiation engine

If your real English-only negotiation backend is not ready yet, you can run the included mock service in [mock_negotiation.py](/C:/Users/shgar/Documents/Playground/mock_negotiation.py).

1. Start the mock service in a separate terminal:

```bash
uvicorn mock_negotiation:app --port 9000 --reload
```

2. Keep this in `.env`:

```env
NEGOTIATION_API_URL=http://localhost:9000/negotiation-engine
```

3. Verify the mock service:

```bash
curl http://localhost:9000/health
```

4. Test it directly:

```bash
curl -X POST http://localhost:9000/negotiation-engine \
  -H "Content-Type: application/json" \
  -d "{\"input\":\"User has not received payment for completed freelance work.\"}"
```

Expected response shape:

```json
{
  "suggestion": "A partial settlement between 60% and 80% of the claimed amount is a reasonable opening position.",
  "settlement_range": "60%-80%",
  "risk_level": "medium",
  "next_step": "Request proof of completed work and propose a time-bound payment plan."
}
```

The multilingual interface only requires the `suggestion` field, so this mock is safe to replace later with the real engine.

## Notes

- The service intentionally does not implement any negotiation logic.
- Translation is provider-based, so you can replace the OpenAI translator with Google Translate or another engine without changing the pipeline.
- `SpeechToTextService` loads Whisper on startup, so first boot can be slow.
- For production, move from SQLite to a managed database and object storage for uploaded files.

## Bonus-ready extension points

- Add WebSocket streaming for real-time transcription and translation.
- Persist confidence scores once the translation provider exposes them.
- Add per-user conversation history views built on top of stored interactions.
