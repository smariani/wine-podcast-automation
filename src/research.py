"""Scarica e filtra notizie recenti da feed RSS italiani sul vino."""

import feedparser
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field


FEEDS = [
    "https://www.gamberorosso.it/feed/",
    "https://www.winenews.it/feed/",
    "https://www.decanter.com/feed/",
]

MAX_AGE_DAYS = 7
MAX_STORIES = 5


@dataclass
class Story:
    title: str
    summary: str
    source: str


@dataclass
class ResearchResult:
    stories: list[Story] = field(default_factory=list)
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def run() -> ResearchResult:
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    stories: list[Story] = []

    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                published = entry.get("published_parsed")
                if published:
                    published_dt = datetime(*published[:6], tzinfo=timezone.utc)
                    if published_dt < cutoff:
                        continue
                stories.append(Story(
                    title=entry.get("title", "").strip(),
                    summary=entry.get("summary", "")[:300].strip(),
                    source=feed.feed.get("title", url),
                ))
                if len(stories) >= MAX_STORIES:
                    break
        except Exception as e:
            print(f"[research] Errore su {url}: {e}")

        if len(stories) >= MAX_STORIES:
            break

    return ResearchResult(stories=stories)
