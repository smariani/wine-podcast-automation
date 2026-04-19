"""Legge file di testo da una cartella Google Drive."""

import os
import json
from dataclasses import dataclass
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
FOLDER_ID = "14S9TxRcBKcTXRMc0nN-zEtMd43U1kISy"


@dataclass
class DriveFile:
    file_id: str
    name: str       # nome completo con data es. "2026-04-20_Cose_e_il_vino.txt"
    title: str      # titolo pulito senza data es. "Cos'è il vino"


def _get_service():
    key_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not key_json:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON non impostata")
    info = json.loads(key_json)
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def _extract_title(filename: str) -> str:
    """Rimuove la data dal nome file e pulisce il titolo.
    Es. '2026-04-20_Cose_e_il_vino.txt' → 'Cos'è il vino'
    """
    name = filename
    if name.endswith(".txt"):
        name = name[:-4]
    # Rimuove prefisso data YYYY-MM-DD_ se presente
    import re
    name = re.sub(r"^\d{4}-\d{2}-\d{2}_?", "", name)
    # Sostituisce underscore con spazi
    name = name.replace("_", " ").strip()
    return name


def list_files() -> list[DriveFile]:
    """Restituisce tutti i file .txt nella cartella, ordinati per nome."""
    service = _get_service()
    query = f"'{FOLDER_ID}' in parents and mimeType='text/plain' and trashed=false"
    result = service.files().list(
        q=query,
        fields="files(id, name)",
        orderBy="name",
    ).execute()

    files = []
    for f in result.get("files", []):
        files.append(DriveFile(
            file_id=f["id"],
            name=f["name"],
            title=_extract_title(f["name"]),
        ))
    return files


def read_file(file: DriveFile) -> tuple[str, str]:
    """Legge il file Drive e restituisce (titolo, testo_tts).

    Gestisce il formato con marcatori di sezione [TITOLO], [REGIA], ecc.
    Il titolo viene letto dalla riga subito dopo [TITOLO].
    Il testo TTS è il contenuto parlato, ripulito da tutti i marcatori.
    """
    import re as _re

    service = _get_service()
    raw = service.files().get_media(fileId=file.file_id).execute()
    content = raw.decode("utf-8").strip()

    # Normalizza line endings
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    # Estrae il titolo dalla riga dopo [TITOLO]
    title_match = _re.search(r"\[TITOLO\]\s*\n([^\[\n]+)", content)
    if title_match:
        title = title_match.group(1).strip()
    else:
        # Fallback: prima riga non-marcatore, altrimenti dal nome file
        first_line = next(
            (l.strip() for l in content.splitlines()
             if l.strip() and not l.strip().startswith("[")),
            ""
        )
        title = first_line if (first_line and len(first_line) <= 120) else file.title

    # Rimuove le sezioni di intestazione [TITOLO], [SOTTOTITOLO], [REGIA]
    # e il testo immediatamente successivo fino al prossimo marcatore
    testo = content
    for section in ["TITOLO", "SOTTOTITOLO", "REGIA"]:
        testo = _re.sub(rf"\[{section}\]\s*\n[^\[]*", "", testo)

    # Rimuove tutti i marcatori [qualsiasi cosa] rimasti (sigla, pausa, note regia)
    testo = _re.sub(r"\[.*?\]", "", testo)

    # Pulizia righe vuote multiple
    testo = _re.sub(r"\n{3,}", "\n\n", testo).strip()

    return title, testo
