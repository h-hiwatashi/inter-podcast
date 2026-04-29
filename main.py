import json
import os
import sys
import tempfile
from datetime import datetime

from config import PROCESSED_URLS_FILE
from fetcher import fetch_new_articles, load_processed_urls
from translator import generate_script
from tts import text_to_mp3
from publisher import upload_mp3_to_release, update_feed


def save_processed_urls(new_urls: list[str]) -> None:
    existing = load_processed_urls()
    updated = list(existing | set(new_urls))
    with open(PROCESSED_URLS_FILE, "w") as f:
        json.dump(updated, f, ensure_ascii=False, indent=2)


def commit_and_push(files: list[str], message: str) -> None:
    files_str = " ".join(files)
    os.system(f"git add {files_str}")
    os.system(f'git commit -m "{message}"')
    os.system("git push")


def main() -> None:
    print("Fetching new articles...")
    articles = fetch_new_articles()

    if not articles:
        print("No new articles found. Exiting.")
        sys.exit(0)

    print(f"Found {len(articles)} new articles.")

    print("Generating podcast script...")
    script = generate_script(articles)
    print(f"Script generated ({len(script)} chars).")

    print("Converting to audio...")
    mp3_bytes = text_to_mp3(script)
    print(f"Audio generated ({len(mp3_bytes)} bytes).")

    now = datetime.utcnow()
    filename = f"episode_{now.strftime('%Y%m%d_%H%M')}.mp3"
    episode_title = f"インテルミラノニュース {now.strftime('%Y/%m/%d %H:%M')} UTC"

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(mp3_bytes)
        tmp_path = tmp.name

    try:
        os.rename(tmp_path, filename)
        print(f"Uploading {filename} to GitHub Releases...")
        mp3_url = upload_mp3_to_release(mp3_bytes, filename, episode_title)
        print(f"Uploaded: {mp3_url}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

    print("Updating feed.xml...")
    update_feed(mp3_url, filename, episode_title)

    print("Saving processed URLs...")
    save_processed_urls([a["url"] for a in articles])

    print("Committing changes...")
    commit_and_push(["feed.xml", PROCESSED_URLS_FILE], f"Add episode: {episode_title}")

    print("Done.")


if __name__ == "__main__":
    main()
