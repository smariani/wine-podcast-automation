"""Carica l'episodio su GitHub Releases e aggiorna il feed RSS su docs/feed.xml."""

import os
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

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

def _init_feed() -> ET.Element:
    """Crea un feed RSS vuoto con i metadati del podcast."""
    ET.register_namespace("itunes", "http://www.itunes.com/dtds/podcast-1.0.dtd")
    ET.register_namespace("atom", "http://www.w3.org/2005/Atom")

    rss = ET.Element("rss", {
        "version": "2.0",
        "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
        "xmlns:atom": "http://www.w3.org/2005/Atom",
    })
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = PODCAST_TITLE
    ET.SubElement(channel, "description").text = PODCAST_DESCRIPTION
    ET.SubElement(channel, "language").text = PODCAST_LANGUAGE
    ET.SubElement(channel, "link").text = PODCAST_LINK
    ET.SubElement(channel, "atom:link", {
        "href": FEED_URL,
        "rel": "self",
        "type": "application/rss+xml",
    })

    image = ET.SubElement(channel, "image")
    ET.SubElement(image, "url").text = COVER_URL
    ET.SubElement(image, "title").text = PODCAST_TITLE
    ET.SubElement(image, "link").text = PODCAST_LINK

    ET.SubElement(channel, "itunes:author").text = PODCAST_AUTHOR
    ET.SubElement(channel, "itunes:image", {"href": COVER_URL})

    itunes_owner = ET.SubElement(channel, "itunes:owner")
    ET.SubElement(itunes_owner, "itunes:name").text = PODCAST_AUTHOR

    return rss


def _load_feed() -> tuple[ET.Element, ET.Element]:
    """Carica il feed esistente o ne crea uno nuovo. Restituisce (rss, channel)."""
    if FEED_PATH.exists():
        tree = ET.parse(FEED_PATH)
        rss = tree.getroot()
        channel = rss.find("channel")
    else:
        rss = _init_feed()
        channel = rss.find("channel")
    return rss, channel


def _add_episode(channel: ET.Element, title: str, description: str, audio_url: str,
                 file_size: int, pub_date: datetime) -> None:
    """Aggiunge un nuovo <item> in cima al canale."""
    item = ET.Element("item")

    ET.SubElement(item, "title").text = title
    ET.SubElement(item, "description").text = description
    ET.SubElement(item, "enclosure", {
        "url": audio_url,
        "length": str(file_size),
        "type": "audio/mpeg",
    })
    ET.SubElement(item, "guid", {"isPermaLink": "false"}).text = audio_url
    ET.SubElement(item, "pubDate").text = format_datetime(pub_date)
    ET.SubElement(item, "itunes:duration").text = "00:10:00"

    # Inserisce il nuovo episodio prima del primo <item> esistente
    items = channel.findall("item")
    if items:
        first_item_index = list(channel).index(items[0])
        channel.insert(first_item_index, item)
    else:
        channel.append(item)


def update_feed(title: str, description: str, audio_url: str,
                file_size: int, pub_date: datetime) -> None:
    """Aggiorna docs/feed.xml con il nuovo episodio."""
    FEED_PATH.parent.mkdir(exist_ok=True)
    rss, channel = _load_feed()
    _add_episode(channel, title, description, audio_url, file_size, pub_date)

    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    tree.write(str(FEED_PATH), encoding="unicode", xml_declaration=True)


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
