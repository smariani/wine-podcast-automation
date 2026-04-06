"""Carica l'episodio su GitHub Releases e aggiorna il feed RSS su docs/feed.xml."""

import os
import re
import subprocess
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

import requests

REPO = os.environ.get("GITHUB_REPO", "smariani/wine-podcast-automation")
FEED_PATH = Path("docs/feed.xml")

PODCAST_TITLE = "La Botte Ubriaca"
PODCAST_DESCRIPTION = "Non il migliore podcast sul vino, ma quello che puoi permetterti"
PODCAST_AUTHOR = "La Botte Ubriaca"
PODCAST_LANGUAGE = "it"
PODCAST_LINK = f"https://github.com/{REPO}"
COVER_URL = f"https://raw.githubusercontent.com/{REPO}/main/assets/cover.jpg"
FEED_URL = f"https://{REPO.split('/')[0]}.github.io/{REPO.split('/')[1]}/feed.xml"


# ── GitHub Releases ──────────────────────────────────────────────────────────

def _github_headers() -> dict:
    token = os.environ["GITHUB_TOKEN"]
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _unique_tag(base_tag: str, headers: dict, api: str) -> str:
    """Restituisce un tag univoco: base_tag, base_tag-2, base_tag-3, ..."""
    existing = {r["tag_name"] for r in requests.get(f"{api}/releases", headers=headers, timeout=30).json()}
    tag, n = base_tag, 2
    while tag in existing:
        tag = f"{base_tag}-{n}"
        n += 1
    return tag


def upload_release(episode_path: Path, tag: str) -> str:
    """Crea una GitHub Release e carica l'MP3. Restituisce l'URL pubblico del file."""
    headers = _github_headers()
    api = f"https://api.github.com/repos/{REPO}"

    tag = _unique_tag(tag, headers, api)

    # Crea la release
    resp = requests.post(
        f"{api}/releases",
        json={"tag_name": tag, "name": f"Episodio {tag}", "draft": False, "prerelease": False},
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    release = resp.json()

    upload_url = release["upload_url"].replace("{?name,label}", "")

    # Carica il file MP3
    with open(episode_path, "rb") as f:
        asset_resp = requests.post(
            upload_url,
            params={"name": episode_path.name},
            headers={**headers, "Content-Type": "audio/mpeg"},
            data=f,
            timeout=120,
        )
        asset_resp.raise_for_status()

    return asset_resp.json()["browser_download_url"]


# ── Feed RSS ──────────────────────────────────────────────────────────────────

_FEED_TEMPLATE = """\
<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{title}</title>
    <description>{description}</description>
    <language>{language}</language>
    <link>{link}</link>
    <atom:link href="{feed_url}" rel="self" type="application/rss+xml" />
    <image>
      <url>{cover_url}</url>
      <title>{title}</title>
      <link>{link}</link>
    </image>
    <itunes:author>{author}</itunes:author>
    <itunes:image href="{cover_url}" />
    <itunes:explicit>false</itunes:explicit>
    <itunes:category text="Society &amp; Culture">
      <itunes:category text="Food" />
    </itunes:category>
    <itunes:owner>
      <itunes:name>{author}</itunes:name>
      <itunes:email>stefano1.mariani@gmail.com</itunes:email>
    </itunes:owner>
{items}  </channel>
</rss>"""

_ITEM_TEMPLATE = """\
    <item>
      <title>{title}</title>
      <description>{description}</description>
      <enclosure url="{audio_url}" length="{file_size}" type="audio/mpeg" />
      <guid isPermaLink="false">{audio_url}</guid>
      <pubDate>{pub_date}</pubDate>
      <itunes:duration>{duration}</itunes:duration>
    </item>
"""


def _existing_items() -> str:
    """Estrae i blocchi <item> dal feed corrente come testo grezzo."""
    if not FEED_PATH.exists():
        return ""
    content = FEED_PATH.read_text(encoding="utf-8")
    blocks = re.findall(r"[ \t]*<item>.*?</item>\n?", content, re.DOTALL)
    return "".join(blocks)


def update_feed(title: str, description: str, audio_url: str,
                file_size: int, pub_date: datetime) -> None:
    """Riscrive docs/feed.xml aggiungendo il nuovo episodio in cima."""
    new_item = _ITEM_TEMPLATE.format(
        title=escape(title),
        description=escape(description),
        audio_url=audio_url,
        file_size=file_size,
        pub_date=format_datetime(pub_date),
        duration="00:10:00",
    )
    all_items = new_item + _existing_items()

    xml = _FEED_TEMPLATE.format(
        title=escape(PODCAST_TITLE),
        description=escape(PODCAST_DESCRIPTION),
        language=PODCAST_LANGUAGE,
        link=PODCAST_LINK,
        feed_url=FEED_URL,
        cover_url=COVER_URL,
        author=escape(PODCAST_AUTHOR),
        items=all_items,
    )

    FEED_PATH.parent.mkdir(exist_ok=True)
    FEED_PATH.write_text(xml, encoding="utf-8")


# ── Git push ──────────────────────────────────────────────────────────────────

def git_push(message: str) -> None:
    """Fa commit di docs/feed.xml e lo pusha su origin/main."""
    token = os.environ["GITHUB_TOKEN"]
    remote_url = f"https://{token}@github.com/{REPO}.git"

    subprocess.run(["git", "add", str(FEED_PATH)], check=True)

    # Se non ci sono modifiche staged, skip del commit
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode != 0:
        subprocess.run(["git", "commit", "-m", message], check=True)

    subprocess.run(["git", "push", remote_url, "main"], check=True)


# ── Entry point ───────────────────────────────────────────────────────────────

def run(episode_path: Path, title: str, script_text: str) -> str:
    """
    Pubblica l'episodio completo:
    1. Carica MP3 su GitHub Releases
    2. Aggiorna docs/feed.xml
    3. Push su GitHub

    Restituisce l'URL pubblico dell'audio.
    """
    tag = episode_path.stem.split("_")[0]  # es. "2026-04-06"
    pub_date = datetime.now(timezone.utc)
    description = script_text[:300].strip() + "…"
    file_size = episode_path.stat().st_size

    audio_url = upload_release(episode_path, tag)
    update_feed(title, description, audio_url, file_size, pub_date)
    git_push(f"ep: {title}")

    return audio_url
