"""
削除したいエピソードを番号で選択して削除するスクリプト。
GitHub Release（MP3）と feed.xml の両方から削除します。

使い方:
  python delete_episodes.py
"""

import os
import subprocess
from lxml import etree
from github import Github
from config import GITHUB_REPO, GITHUB_TOKEN, FEED_FILE


def get_releases(repo):
    releases = []
    for r in repo.get_releases():
        assets = list(r.get_assets())
        mp3 = next((a for a in assets if a.name.endswith(".mp3")), None)
        releases.append({"release": r, "mp3": mp3})
    releases.sort(key=lambda x: x["release"].created_at, reverse=True)
    return releases


def select_episodes(releases):
    print("\n削除するエピソードを選択してください（複数の場合はカンマ区切り例: 1,3,5）\n")
    for i, item in enumerate(releases, 1):
        r = item["release"]
        size = f"{item['mp3'].size // 1024}KB" if item["mp3"] else "asset不明"
        print(f"  {i:2}. {r.title}  [{size}]")

    print()
    raw = input("番号を入力 (Enterでキャンセル): ").strip()
    if not raw:
        return []

    selected = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(releases):
                selected.append(releases[idx])
    return selected


def confirm(selected):
    print("\n以下のエピソードを削除します:\n")
    for item in selected:
        print(f"  - {item['release'].title}")
    print()
    ans = input("実行しますか？ [y/N]: ").strip().lower()
    return ans == "y"


def remove_from_feed(mp3_urls: set):
    if not os.path.exists(FEED_FILE):
        return
    tree = etree.parse(FEED_FILE)
    rss = tree.getroot()
    channel = rss.find("channel")
    for item in list(channel.findall("item")):
        enc = item.find("enclosure")
        if enc is not None and enc.get("url") in mp3_urls:
            channel.remove(item)
    tree.write(FEED_FILE, pretty_print=True, xml_declaration=True, encoding="UTF-8")


def delete_release_and_tag(repo, release):
    tag_name = release.tag_name
    release.delete_release()
    try:
        ref = repo.get_git_ref(f"tags/{tag_name}")
        ref.delete()
    except Exception:
        pass


def main():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    print("エピソード一覧を取得中...")
    releases = get_releases(repo)
    if not releases:
        print("エピソードが見つかりません。")
        return

    selected = select_episodes(releases)
    if not selected:
        print("キャンセルしました。")
        return

    if not confirm(selected):
        print("キャンセルしました。")
        return

    mp3_urls = set()
    for item in selected:
        r = item["release"]
        print(f"削除中: {r.title}")
        if item["mp3"]:
            mp3_urls.add(item["mp3"].browser_download_url)
        delete_release_and_tag(repo, r)

    print("feed.xml を更新中...")
    remove_from_feed(mp3_urls)

    print("git commit & push 中...")
    subprocess.run(["git", "add", FEED_FILE], check=True)
    subprocess.run(["git", "commit", "-m", f"Remove {len(selected)} episode(s)"], check=True)
    subprocess.run(["git", "push"], check=True)

    print(f"\n完了: {len(selected)} 件削除しました。")


if __name__ == "__main__":
    main()
