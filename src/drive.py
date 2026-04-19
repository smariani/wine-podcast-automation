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

    Convenzione: se la prima riga è breve (<=120 chars, niente punto finale),
    viene usata come titolo e rimossa dal testo TTS.
    Altrimenti il titolo viene derivato dal nome file come fallback.
    """
    service = _get_service()
    raw = service.files().get_media(fileId=file.file_id).execute()
    content = raw.decode("utf-8").strip()

    lines = content.splitlines()
    first_line = lines[0].strip() if lines else ""

    if first_line and len(first_line) <= 120 and not first_line.endswith("."):
        title = first_line
        testo = "\n".join(lines[1:]).strip()
    else:
        title = file.title
        testo = content

    return title, testo
