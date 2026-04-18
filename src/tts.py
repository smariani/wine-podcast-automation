"""Converte il testo in audio MP3 usando ElevenLabs."""

import os
from pathlib import Path
from elevenlabs.client import ElevenLabs
from elevenlabs import save

# Voce di default: "Violetta" — italiana (modificabile via ELEVENLABS_VOICE_ID)
DEFAULT_VOICE_ID = "gfKKsLN1k0oYYN9n2dXX"
MODEL_ID = "eleven_multilingual_v2"


def run(text: str, output_path: Path) -> Path:
    api_key = os.environ["ELEVENLABS_API_KEY"]
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)

    client = ElevenLabs(api_key=api_key)
    audio = client.generate(
        text=text,
        voice=voice_id,
        model=MODEL_ID,
    )
    save(audio, str(output_path))
    return output_path
