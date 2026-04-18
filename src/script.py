"""Genera il testo parlato dell'episodio usando Groq."""

import os
from groq import Groq
from src.research import ResearchResult
from src.episode_format import EpisodeFormat

WORDS_PER_MINUTE = 130
TARGET_MINUTES = 10

SYSTEM_PROMPT = """\
Sei il conduttore di un podcast italiano sul vino chiamato "Il Sommelier Digitale".
Il tuo stile è colto ma accessibile, appassionato e con una punta di ironia.
Scrivi SOLO il testo parlato — niente titoli, niente sezioni, niente indicazioni di regia.
Usa un linguaggio naturale, come se stessi parlando direttamente con gli ascoltatori.
Non usare elenchi puntati. Solo prosa fluente, adatta a essere letta ad alta voce.
"""


def _build_prompt(result: ResearchResult, fmt: EpisodeFormat) -> str:
    target_words = TARGET_MINUTES * WORDS_PER_MINUTE

    if result.stories:
        notizie_parts = []
        for s in result.stories:
            parte = f"- {s.title} ({s.source}): {s.summary}"
            if s.body:
                parte += f"\n  Approfondimento: {s.body}"
            notizie_parts.append(parte)
        notizie_block = "Notizie recenti dal mondo del vino:\n" + "\n".join(notizie_parts)
    else:
        notizie_block = "Non ci sono notizie recenti disponibili questa settimana."

    return f"""\
Crea uno script completo per un episodio del podcast "Il Sommelier Digitale".
Formato di oggi: "{fmt.label}".

{notizie_block}

Istruzioni per questo episodio:
{fmt.instructions}

Lo script deve:
- Aprire con un saluto caldo e introdurre il tema dell'episodio
- Sviluppare il contenuto principale con profondità e curiosità
- Includere almeno un aneddoto, un dato storico o una curiosità poco nota
- Concludere con un consiglio pratico: una bottiglia o un abbinamento da provare
- Essere lungo esattamente circa {target_words} parole ({TARGET_MINUTES} minuti di parlato)

È fondamentale raggiungere la lunghezza richiesta: non fermarti prima.
Scrivi solo il testo parlato, senza titoli o marcatori di sezione.
"""


def generate(result: ResearchResult, fmt: EpisodeFormat) -> str:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_prompt(result, fmt)},
        ],
        temperature=0.8,
        max_tokens=4096,
    )

    return response.choices[0].message.content.strip()
