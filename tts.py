from google.cloud import texttospeech
from config import TTS_VOICE

BYTE_LIMIT = 4500  # 5000バイト上限に対して余裕を持たせる


def _split_text(text: str) -> list[str]:
    sentences = []
    current = ""
    for char in text:
        current += char
        if char in ("。", "、", "\n") and len(current.encode("utf-8")) >= 100:
            sentences.append(current)
            current = ""
    if current:
        sentences.append(current)

    chunks = []
    current_chunk = ""
    for sentence in sentences:
        candidate = current_chunk + sentence
        if len(candidate.encode("utf-8")) > BYTE_LIMIT:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence
        else:
            current_chunk = candidate
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def text_to_mp3(script: str) -> bytes:
    client = texttospeech.TextToSpeechClient()

    voice = texttospeech.VoiceSelectionParams(
        language_code="ja-JP",
        name=TTS_VOICE,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.2,
        pitch=0.0,
    )

    chunks = _split_text(script)
    audio_parts = []
    for chunk in chunks:
        response = client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=chunk),
            voice=voice,
            audio_config=audio_config,
        )
        audio_parts.append(response.audio_content)

    return b"".join(audio_parts)
