"""Pubblica un episodio con testo fornito manualmente."""
from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
from src import tts, publisher

testo = Path("output/2026-04-19_Perche_il_vino_parla.txt").read_text(encoding="utf-8")
episode_path = Path("output/2026-04-19_episodio.mp3")

print("Sintetizzo la voce...")
tts.run(testo, episode_path)
size_mb = round(episode_path.stat().st_size / 1024 / 1024, 1)
print(f"Salvato: {episode_path} ({size_mb} MB)")

print("Carico e pubblico...")
title = "La Botte Ubriaca – Perché il vino parla"
url = publisher.run(episode_path, title, testo)
print(f"Pubblicato: {url}")
