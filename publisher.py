import os
import tempfile
from datetime import datetime, timezone
from lxml import etree
from github import Github
from config import (
    GITHUB_REPO, GITHUB_TOKEN, FEED_FILE,
    PODCAST_TITLE, PODCAST_DESCRIPTION, PODCAST_LANGUAGE, PODCAST_AUTHOR,
    MAX_FEED_EPISODES,
)

FEED_BASE_URL = f"https://h-hiwatashi.github.io/inter-podcast"


def upload_mp3_to_release(mp3_bytes: bytes, filename: str, episode_title: str) -> str:
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    tag = f"episode-{filename.replace('.mp3', '')}"
    release = repo.create_git_release(
        tag=tag,
        name=episode_title,
        message=f"Auto-generated podcast episode: {episode_title}",
    )

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(mp3_bytes)
        tmp_path = tmp.name

    try:
        asset = release.upload_asset(
            path=tmp_path,
            content_type="audio/mpeg",
            name=filename,
        )
    finally:
        os.unlink(tmp_path)

    return asset.browser_download_url


def _build_empty_feed() -> etree._Element:
    nsmap = {
        None: None,
        "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
        "content": "http://purl.org/rss/1.0/modules/content/",
    }
    rss = etree.Element("rss", version="2.0", nsmap={
        "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
    })
    channel = etree.SubElement(rss, "channel")

    def add(parent, tag, text):
        el = etree.SubElement(parent, tag)
        el.text = text
        return el

    ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"
    add(channel, "title", PODCAST_TITLE)
    add(channel, "description", PODCAST_DESCRIPTION)
    add(channel, "language", PODCAST_LANGUAGE)
    add(channel, "link", FEED_BASE_URL)
    add(channel, f"{{{ITUNES}}}author", PODCAST_AUTHOR)
    add(channel, f"{{{ITUNES}}}explicit", "false")

    image = etree.SubElement(channel, f"{{{ITUNES}}}image")
    image.set("href", f"{FEED_BASE_URL}/cover.jpg")

    return rss


def update_feed(mp3_url: str, filename: str, episode_title: str, duration_hint: int = 300) -> None:
    ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"

    if os.path.exists(FEED_FILE):
        tree = etree.parse(FEED_FILE)
        rss = tree.getroot()
        channel = rss.find("channel")
    else:
        rss = _build_empty_feed()
        channel = rss.find("channel")

    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

    item = etree.Element("item")

    def add(parent, tag, text):
        el = etree.SubElement(parent, tag)
        el.text = text
        return el

    add(item, "title", episode_title)
    add(item, "pubDate", now)
    add(item, f"{{{ITUNES}}}duration", str(duration_hint))

    guid = etree.SubElement(item, "guid")
    guid.text = mp3_url
    guid.set("isPermaLink", "false")

    enclosure = etree.SubElement(item, "enclosure")
    enclosure.set("url", mp3_url)
    enclosure.set("type", "audio/mpeg")
    enclosure.set("length", "0")

    # Insert as first item (newest first)
    first_item = channel.find("item")
    if first_item is not None:
        channel.insert(list(channel).index(first_item), item)
    else:
        channel.append(item)

    # Keep only latest MAX_FEED_EPISODES items
    items = channel.findall("item")
    for old_item in items[MAX_FEED_EPISODES:]:
        channel.remove(old_item)

    tree = etree.ElementTree(rss)
    tree.write(FEED_FILE, pretty_print=True, xml_declaration=True, encoding="UTF-8")
