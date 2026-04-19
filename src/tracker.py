"""Tiene traccia degli episodi già pubblicati."""

import json
from pathlib import Path

TRACKER_FILE = Path("published.json")


def load() -> set[str]:
    """Restituisce l'insieme dei nomi file già pubblicati."""
    if not TRACKER_FILE.exists():
        return set()
    return set(json.loads(TRACKER_FILE.read_text(encoding="utf-8")))


def mark_published(filename: str) -> None:
    """Aggiunge un file all'elenco dei pubblicati e salva."""
    published = load()
    published.add(filename)
    TRACKER_FILE.write_text(
        json.dumps(sorted(published), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def is_published(filename: str) -> bool:
    return filename in load()
