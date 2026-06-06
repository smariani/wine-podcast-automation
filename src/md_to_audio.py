"""Legge file .md da Google Drive, sintetizza voce e salva MP3 su Drive."""

import re
from pathlib import Path
from src import drive, tts

SOURCE_ROOT_ID = "1Z8IQgRiu2yM64zuv1tOpeThDte5dy169"
AUDIO_ROOT_ID = "1ZZRMuu47-Q8VyKmMV1XnCYkmA_LlyDND"
TMP_DIR = Path("tmp_audio")

_WEEK_RE = re.compile(r"^\d{4}-W\d{2}$")


def _strip_markdown(text: str) -> str:
    """Rimuove sintassi markdown per ottenere testo parlabile pulito."""
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)      # titoli
    text = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", text)              # grassetto/corsivo
    text = re.sub(r"_{1,3}(.+?)_{1,3}", r"\1", text)
    text = re.sub(r"!\[.*?\]\(.+?\)", "", text)                      # immagini
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)                  # link
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)           # blocchi codice
    text = re.sub(r"`(.+?)`", r"\1", text)                           # inline code
    text = re.sub(r"^-{3,}$", "", text, flags=re.MULTILINE)          # separatori
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)            # citazioni
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def process_week(week_name: str, week_folder_id: str, test_mode: bool = False) -> str:
    """Processa una singola settimana. Restituisce l'ID del file audio caricato su Drive."""
    print(f"  [md]    Leggo {week_name}...")
    md_content = drive.read_md_file(week_folder_id)
    text = _strip_markdown(md_content)

    TMP_DIR.mkdir(exist_ok=True)
    mp3_name = f"{week_name}.mp3"
    local_path = TMP_DIR / mp3_name

    print(f"  [tts]   Sintetizzo → {mp3_name}...")
    tts.run(text, local_path, test_mode=test_mode)
    size_mb = round(local_path.stat().st_size / 1024 / 1024, 2)
    print(f"          Audio locale: {local_path} ({size_mb} MB)")

    print(f"  [drive] Carico su Drive in {week_name}/...")
    dest_folder_id = drive.get_or_create_subfolder(AUDIO_ROOT_ID, week_name)
    file_id = drive.upload_audio(local_path, dest_folder_id)

    local_path.unlink()
    return file_id


def run(week_filter: str | None = None, test_mode: bool = False) -> None:
    folders = drive.list_week_folders(SOURCE_ROOT_ID)
    folders = [f for f in folders if _WEEK_RE.match(f["name"])]
    folders.sort(key=lambda f: f["name"])

    if week_filter:
        folders = [f for f in folders if f["name"] == week_filter]
        if not folders:
            raise ValueError(f"Cartella settimana '{week_filter}' non trovata in Drive.")

    print(f"Settimane trovate: {[f['name'] for f in folders]}")
    for folder in folders:
        file_id = process_week(folder["name"], folder["id"], test_mode=test_mode)
        print(f"  OK: {folder['name']} → Drive file ID {file_id}\n")
