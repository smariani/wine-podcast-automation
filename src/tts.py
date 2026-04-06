"""Converte il testo in audio MP3 usando edge-tts."""

import asyncio
from pathlib import Path
import edge_tts

# Voce italiana di alta qualità disponibile in edge-tts
VOICE = "it-IT-DiegoNeural"


async def _synthesize(text: str, output_path: Path) -> None:
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(str(output_path))


def run(text: str, output_path: Path) -> Path:
    asyncio.run(_synthesize(text, output_path))
    return output_path
