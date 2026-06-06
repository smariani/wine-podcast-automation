"""CLI: legge .md da Google Drive, sintetizza con TTS, carica MP3 su Drive."""

import argparse
import os
from src import md_to_audio


def main():
    parser = argparse.ArgumentParser(
        description="MD → TTS → Drive. Elabora le cartelle settimana dalla sorgente Drive."
    )
    parser.add_argument(
        "--week",
        metavar="2026-W22",
        help="Processa solo questa settimana (es. 2026-W22). Senza flag: tutte le settimane.",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Modalità test: usa edge-tts gratuito, sintetizza solo i primi 500 caratteri.",
    )
    args = parser.parse_args()

    test_mode = args.test or os.environ.get("TTS_TEST_MODE", "").lower() in ("1", "true")
    if test_mode:
        print("[MODALITÀ TEST — edge-tts, primi 500 caratteri]\n")

    md_to_audio.run(week_filter=args.week, test_mode=test_mode)
    print("Completato.")


if __name__ == "__main__":
    main()
