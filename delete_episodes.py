"""
削除したいエピソードを番号で選択して削除するスクリプト。
GitHub Release（MP3）と feed.xml の両方から削除します。

ローカル対話モード:
  python delete_episodes.py

CIモード（番号指定）:
  python delete_episodes.py --list
  python delete_episodes.py --delete 1,3,5
"""

import argparse
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


def print_list(releases):
    print("\n# エピソード一覧\n")
    for i, item in enumerate(releases, 1):
        r = item["release"]
        size = f"{item['mp3'].size // 1024}KB" if item["mp3"] else "asset不明"
        print(f"  {i:2}. {r.title}  [{size}]")
    print()


def select_by_input(releases):
    print_list(releases)
    print("削除するエピソードを選択してください（複数の場合はカンマ区切り例: 1,3,5）\n")
    raw = input("番号を入力 (Enterでキャンセル): ").strip()
    if not raw:
        return []
    return parse_numbers(raw, releases)


def parse_numbers(raw: str, releases: list) -> list:
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


def do_delete(selected, repo):
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true", help="エピソード一覧を表示して終了")
    parser.add_argument("--delete", metavar="NUMBERS", help="削除する番号（カンマ区切り例: 1,3,5）")
    args = parser.parse_args()

    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    print("エピソード一覧を取得中...")
    releases = get_releases(repo)
    if not releases:
        print("エピソードが見つかりません。")
        return

    if args.list:
        print_list(releases)
        return

    if args.delete:
        selected = parse_numbers(args.delete, releases)
        if not selected:
            print("有効な番号が見つかりません。")
            return
        print("\n以下のエピソードを削除します:\n")
        for item in selected:
            print(f"  - {item['release'].title}")
        do_delete(selected, repo)
        return

    # 対話モード
    selected = select_by_input(releases)
    if not selected:
        print("キャンセルしました。")
        return
    if not confirm(selected):
        print("キャンセルしました。")
        return
    do_delete(selected, repo)


if __name__ == "__main__":
    main()
