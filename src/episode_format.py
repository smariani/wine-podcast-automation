"""Definisce il formato dell'episodio in base al giorno della settimana."""

from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass
class EpisodeFormat:
    name: str
    label: str        # usato nel titolo episodio
    instructions: str # istruzioni aggiuntive per lo script


FORMATS = [
    EpisodeFormat(
        name="notizie",
        label="Notizie dalla Vigna",
        instructions=(
            "Commenta le notizie recenti in modo approfondito. "
            "Per ogni notizia offri contesto storico o tecnico che la arricchisce."
        ),
    ),
    EpisodeFormat(
        name="regione",
        label="Viaggio in una Regione",
        instructions=(
            "Scegli una delle regioni vinicole italiane citate nelle notizie (o una a tua scelta "
            "se non emergono chiaramente) e dedicale l'episodio: storia, terroir, vitigni autoctoni, "
            "produttori da ricordare, abbinamenti tipici regionali."
        ),
    ),
    EpisodeFormat(
        name="vitigno",
        label="Il Vitigno del Giorno",
        instructions=(
            "Scegli un vitigno — italiano o internazionale — e raccontalo come un personaggio: "
            "origini, caratteristiche organolettiche, dove si esprime meglio, aneddoti curiosi, "
            "bottiglie iconiche. Le notizie possono fare da spunto ma non devono dominare."
        ),
    ),
    EpisodeFormat(
        name="abbinamento",
        label="Arte degli Abbinamenti",
        instructions=(
            "Costruisci l'episodio attorno al tema degli abbinamenti cibo-vino. "
            "Parti da un piatto o ingrediente di stagione, ragiona sui principi dell'abbinamento "
            "(concordanza, contrapposizione, territorialità) e proponi tre abbinamenti concreti "
            "con bottiglie specifiche."
        ),
    ),
    EpisodeFormat(
        name="annata",
        label="La Parola all'Annata",
        instructions=(
            "Parla di un'annata vinicola notevole — recente o storica — raccontando le condizioni "
            "climatiche, come hanno influenzato i vini, quali zone hanno eccellso, "
            "cosa cercare ancora in cantina e cosa invece è già al suo apice."
        ),
    ),
    EpisodeFormat(
        name="notizie",
        label="Notizie dalla Vigna",
        instructions=(
            "Commenta le notizie recenti in modo approfondito. "
            "Per ogni notizia offri contesto storico o tecnico che la arricchisce."
        ),
    ),
    EpisodeFormat(
        name="produttore",
        label="Ritratto di Produttore",
        instructions=(
            "Scegli un produttore vinicolo — artigiano o grande maison — e raccontane la storia, "
            "la filosofia, i vini simbolo, le scelte in vigna e in cantina. "
            "Le notizie possono fornire spunti ma l'episodio è un ritratto umano e produttivo."
        ),
    ),
]


def get_format(date: datetime | None = None) -> EpisodeFormat:
    """Restituisce il formato del giorno basandosi sul giorno della settimana (0=lun, 6=dom)."""
    if date is None:
        date = datetime.now(timezone.utc)
    return FORMATS[date.weekday()]
