"""Orchestra research → script → tts → publisher in sequenza."""

from datetime import datetime, timezone
from pathlib import Path

from src import research, script, tts, publisher

OUTPUT_DIR = Path("output")
PODCAST_TITLE = "La Botte Ubriaca"


def run() -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    slug = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    episode_path = OUTPUT_DIR / f"{slug}_episodio.mp3"
    title = f"{PODCAST_TITLE} – {slug}"

    print("[1/5] Scarico notizie RSS...")
    result = research.run()
    print(f"      {len(result.stories)} notizie trovate")

    print("[2/5] Genero lo script...")
    testo = script.generate(result)
    parole = len(testo.split())
    print(f"      {parole} parole (~{round(parole / 130, 1)} min)")

    print("[3/5] Sintetizzo la voce...")
    tts.run(testo, episode_path)
    size_mb = round(episode_path.stat().st_size / 1024 / 1024, 1)
    print(f"      Salvato: {episode_path} ({size_mb} MB)")

    print("[4/5] Carico MP3 su GitHub Releases...")
    audio_url = publisher.run(episode_path, title, testo)
    print(f"      {audio_url}")

    print("[5/5] Feed RSS aggiornato e pushato.")

    return episode_path
