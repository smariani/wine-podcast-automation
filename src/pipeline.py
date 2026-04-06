"""Orchestra research → script → tts in sequenza."""

from datetime import datetime, timezone
from pathlib import Path

from src import research, script, tts

OUTPUT_DIR = Path("output")


def run() -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    slug = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    episode_path = OUTPUT_DIR / f"{slug}_episodio.mp3"

    print("[1/3] Scarico notizie RSS...")
    result = research.run()
    print(f"      {len(result.stories)} notizie trovate")

    print("[2/3] Genero lo script...")
    testo = script.generate(result)
    parole = len(testo.split())
    print(f"      {parole} parole (~{round(parole / 130, 1)} min)")

    print("[3/3] Sintetizzo la voce...")
    tts.run(testo, episode_path)
    size_mb = round(episode_path.stat().st_size / 1024 / 1024, 1)
    print(f"      Salvato: {episode_path} ({size_mb} MB)")

    return episode_path
