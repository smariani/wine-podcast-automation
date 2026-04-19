"""Converte il testo in audio MP3 usando ElevenLabs."""

import os
import re
from pathlib import Path
from elevenlabs.client import ElevenLabs
from elevenlabs import save
from elevenlabs.types import VoiceSettings

DEFAULT_VOICE_ID = "vh8ugQnSUeaDxwMfmFcx"
MODEL_ID = "eleven_multilingual_v2"

# Parametri voce — ottimizzati per parlato italiano fluente e naturale
VOICE_SETTINGS = VoiceSettings(
    stability=0.45,          # variazione naturale, non monotono
    similarity_boost=0.85,   # fedeltà alta al clone vocale
    style=0.35,              # espressività moderata
    use_speaker_boost=True,  # chiarezza vocale migliorata
)


def _clean_text(text: str) -> str:
    """Rimuove indicazioni di regia e normalizza il testo per TTS."""
    # Rimuove tutto ciò che è tra parentesi quadre [...]
    text = re.sub(r"\[.*?\]", "", text)
    # Collassa righe vuote multiple in una sola
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


TEST_CHARS = 500  # caratteri sintetizzati in modalità test


def _run_test(text: str, output_path: Path) -> None:
    """Sintesi gratuita con edge-tts per test pipeline."""
    import asyncio
    import edge_tts
    async def _synth():
        communicate = edge_tts.Communicate(text[:500], "it-IT-DiegoNeural")
        await communicate.save(str(output_path))
    asyncio.run(_synth())


def run(text: str, output_path: Path, test_mode: bool = False) -> Path:
    text = _clean_text(text)

    if test_mode:
        _run_test(text, output_path)
        return output_path

    api_key = os.environ["ELEVENLABS_API_KEY"]
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)

    client = ElevenLabs(api_key=api_key)
    audio = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id=MODEL_ID,
        voice_settings=VOICE_SETTINGS,
        output_format="mp3_44100_128",
    )
    save(audio, str(output_path))
    return output_path
