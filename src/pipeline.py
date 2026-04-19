"""Orchestra Drive → tts → publisher in sequenza."""

from datetime import datetime, timezone
from pathlib import Path
import re

import os
from src import tts, publisher, tracker
from src.drive import list_files, read_file

OUTPUT_DIR = Path("output")
PODCAST_TITLE = "La Botte Ubriaca"


def _safe_filename(title: str) -> str:
    return re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")[:60]


def run() -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    slug = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print("[1/4] Cerco il prossimo episodio su Google Drive...")
    files = list_files()
    if not files:
        raise ValueError("Nessun file trovato nella cartella Google Drive.")

    next_file = next((f for f in files if not tracker.is_published(f.name)), None)
    if next_file is None:
        raise ValueError("Tutti gli episodi sono già stati pubblicati.")

    print(f"      File: {next_file.name}")
    print(f"      Titolo: {next_file.title}")

    titolo_episodio, testo = read_file(next_file)
    title = f"{PODCAST_TITLE} – {titolo_episodio}"

    episode_path = OUTPUT_DIR / f"{slug}_episodio.mp3"
    script_path = OUTPUT_DIR / f"{slug}_{_safe_filename(next_file.title)}.txt"
    script_path.write_text(testo, encoding="utf-8")

    test_mode = os.environ.get("TTS_TEST_MODE", "").lower() in ("1", "true")
    if test_mode:
        print("[2/4] Sintetizzo la voce... [modalità test — primi 500 char]")
    else:
        print("[2/4] Sintetizzo la voce...")
    tts.run(testo, episode_path, test_mode=test_mode)
    size_mb = round(episode_path.stat().st_size / 1024 / 1024, 1)
    print(f"      Salvato: {episode_path} ({size_mb} MB)")

    print("[3/4] Carico MP3 su GitHub Releases...")
    audio_url = publisher.run(episode_path, title, testo)
    print(f"      {audio_url}")

    print("[4/4] Aggiorno tracker e feed RSS.")
    tracker.mark_published(next_file.name)

    return episode_path
