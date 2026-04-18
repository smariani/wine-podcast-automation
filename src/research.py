"""Scarica e filtra notizie recenti da feed RSS italiani sul vino."""

import re
import requests
import feedparser
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field


FEEDS = [
    "https://www.gamberorosso.it/feed/",
    "https://www.winenews.it/feed/",
    "https://www.decanter.com/feed/",
    "https://www.doctorwine.it/feed/",
    "https://www.winesurf.it/feed/",
    "https://italianwinereview.com/feed/",
]

MAX_AGE_DAYS = 7
MAX_STORIES = 8
SUMMARY_MAX_CHARS = 700
BODY_MAX_CHARS = 1200
FETCH_TIMEOUT = 8


@dataclass
class Story:
    title: str
    summary: str
    source: str
    body: str = ""


@dataclass
class ResearchResult:
    stories: list[Story] = field(default_factory=list)
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _fetch_body(url: str) -> str:
    try:
        resp = requests.get(url, timeout=FETCH_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return ""
        # Estrae il testo grezzo dall'HTML, escludendo script e style
        html = re.sub(r"<(script|style)[^>]*>.*?</(script|style)>", "", resp.text, flags=re.S)
        # Cerca il contenuto principale (article, main, o body)
        for tag in ["article", "main"]:
            match = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", html, re.S)
            if match:
                return _strip_html(match.group(1))[:BODY_MAX_CHARS]
        return ""
    except Exception:
        return ""


def run() -> ResearchResult:
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    stories: list[Story] = []

    for url in FEEDS:
        if len(stories) >= MAX_STORIES:
            break
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if len(stories) >= MAX_STORIES:
                    break
                published = entry.get("published_parsed")
                if published:
                    published_dt = datetime(*published[:6], tzinfo=timezone.utc)
                    if published_dt < cutoff:
                        continue
                summary = _strip_html(entry.get("summary", ""))[:SUMMARY_MAX_CHARS]
                link = entry.get("link", "")
                body = _fetch_body(link) if link else ""
                stories.append(Story(
                    title=entry.get("title", "").strip(),
                    summary=summary,
                    source=feed.feed.get("title", url),
                    body=body,
                ))
        except Exception as e:
            print(f"[research] Errore su {url}: {e}")

    return ResearchResult(stories=stories)
