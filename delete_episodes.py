"""
エピソードの削除・非公開・再公開を行うスクリプト。

ローカル対話モード:
  python delete_episodes.py

CIモード:
  python delete_episodes.py --list
  python delete_episodes.py --list-hidden
  python delete_episodes.py --delete 1,3,5
  python delete_episodes.py --hide 1,3,5
  python delete_episodes.py --show 1,3,5
"""

import argparse
import os
import subprocess
from datetime import timezone
from lxml import etree
from github import Github
from config import GITHUB_REPO, GITHUB_TOKEN, FEED_FILE

ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"


def get_releases(repo, draft=False):
    releases = []
    for r in repo.get_releases():
        if r.draft != draft:
            continue
        assets = list(r.get_assets())
        mp3 = next((a for a in assets if a.name.endswith(".mp3")), None)
        releases.append({"release": r, "mp3": mp3})
    releases.sort(key=lambda x: x["release"].created_at, reverse=True)
    return releases


def print_list(releases, label="公開中"):
    print(f"\n# エピソード一覧（{label}）\n")
    if not releases:
        print("  （なし）\n")
        return
    for i, item in enumerate(releases, 1):
        r = item["release"]
        size = f"{item['mp3'].size // 1024}KB" if item["mp3"] else "asset不明"
        print(f"  {i:2}. {r.title}  [{size}]")
    print()


def parse_numbers(raw: str, releases: list) -> list:
    selected = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(releases):
                selected.append(releases[idx])
    return selected


def select_by_input(releases, prompt):
    print_list(releases)
    raw = input(f"{prompt}（カンマ区切り例: 1,3,5 / Enterでキャンセル）: ").strip()
    if not raw:
        return []
    return parse_numbers(raw, releases)


def confirm(selected, action_label):
    print(f"\n以下のエピソードを{action_label}します:\n")
    for item in selected:
        print(f"  - {item['release'].title}")
    print()
    ans = input("実行しますか？ [y/N]: ").strip().lower()
    return ans == "y"


# --- feed.xml 操作 ---

def remove_from_feed(mp3_urls: set):
    if not os.path.exists(FEED_FILE):
        return
    tree = etree.parse(FEED_FILE)
    channel = tree.getroot().find("channel")
    for item in list(channel.findall("item")):
        enc = item.find("enclosure")
        if enc is not None and enc.get("url") in mp3_urls:
            channel.remove(item)
    tree.write(FEED_FILE, pretty_print=True, xml_declaration=True, encoding="UTF-8")


def add_to_feed(episodes: list):
    """episodes: list of {"release": r, "mp3": asset} を新しい順にfeed.xmlへ挿入"""
    if not os.path.exists(FEED_FILE):
        return
    tree = etree.parse(FEED_FILE)
    channel = tree.getroot().find("channel")

    for ep in episodes:
        r = ep["release"]
        mp3 = ep["mp3"]
        if not mp3:
            continue

        url = mp3.browser_download_url
        size = mp3.size
        pub_date = r.created_at.astimezone(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

        # 既に同じURLのitemがあればスキップ
        existing_urls = {
            item.find("enclosure").get("url")
            for item in channel.findall("item")
            if item.find("enclosure") is not None
        }
        if url in existing_urls:
            continue

        item = etree.Element("item")
        _add(item, "title", r.title)
        _add(item, "pubDate", pub_date)
        _add(item, f"{{{ITUNES}}}duration", "300")
        guid = etree.SubElement(item, "guid")
        guid.text = url
        guid.set("isPermaLink", "false")
        enc = etree.SubElement(item, "enclosure")
        enc.set("url", url)
        enc.set("type", "audio/mpeg")
        enc.set("length", str(size))

        # 日付順を保って挿入
        inserted = False
        for existing in channel.findall("item"):
            existing_date = existing.findtext("pubDate", "")
            if pub_date >= existing_date:
                channel.insert(list(channel).index(existing), item)
                inserted = True
                break
        if not inserted:
            channel.append(item)

    tree.write(FEED_FILE, pretty_print=True, xml_declaration=True, encoding="UTF-8")


def _add(parent, tag, text):
    el = etree.SubElement(parent, tag)
    el.text = text
    return el


# --- GitHub Release 操作 ---

def delete_release_and_tag(repo, release):
    tag_name = release.tag_name
    release.delete_release()
    try:
        repo.get_git_ref(f"tags/{tag_name}").delete()
    except Exception:
        pass


def set_draft(release, draft: bool):
    release.update_release(
        name=release.title,
        message=release.body or "",
        draft=draft,
    )


# --- アクション ---

def do_delete(selected, repo):
    mp3_urls = {item["mp3"].browser_download_url for item in selected if item["mp3"]}
    for item in selected:
        print(f"削除中: {item['release'].title}")
        delete_release_and_tag(repo, item["release"])
    _update_feed_and_push(lambda: remove_from_feed(mp3_urls), len(selected), "Remove")


def do_hide(selected, repo):
    mp3_urls = {item["mp3"].browser_download_url for item in selected if item["mp3"]}
    for item in selected:
        print(f"非公開: {item['release'].title}")
        set_draft(item["release"], draft=True)
    _update_feed_and_push(lambda: remove_from_feed(mp3_urls), len(selected), "Hide")


def do_show(selected, repo):
    for item in selected:
        print(f"再公開: {item['release'].title}")
        set_draft(item["release"], draft=False)
    _update_feed_and_push(lambda: add_to_feed(selected), len(selected), "Show")


def _update_feed_and_push(feed_fn, count, verb):
    print("feed.xml を更新中...")
    feed_fn()
    subprocess.run(["git", "add", FEED_FILE], check=True)
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        capture_output=True,
    )
    if result.returncode != 0:
        subprocess.run(["git", "commit", "-m", f"{verb} {count} episode(s)"], check=True)
        subprocess.run(["git", "push"], check=True)
    print(f"\n完了: {count} 件処理しました。")


# --- メイン ---

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--list-hidden", action="store_true")
    parser.add_argument("--delete", metavar="NUMBERS")
    parser.add_argument("--hide", metavar="NUMBERS")
    parser.add_argument("--show", metavar="NUMBERS")
    args = parser.parse_args()

    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    if args.list:
        print("公開中エピソードを取得中...")
        print_list(get_releases(repo, draft=False), "公開中")
        return

    if args.list_hidden:
        print("非公開エピソードを取得中...")
        print_list(get_releases(repo, draft=True), "非公開")
        return

    if args.delete:
        releases = get_releases(repo, draft=False)
        selected = parse_numbers(args.delete, releases)
        if not selected:
            print("有効な番号が見つかりません。")
            return
        for item in selected:
            print(f"削除対象: {item['release'].title}")
        do_delete(selected, repo)
        return

    if args.hide:
        releases = get_releases(repo, draft=False)
        selected = parse_numbers(args.hide, releases)
        if not selected:
            print("有効な番号が見つかりません。")
            return
        for item in selected:
            print(f"非公開対象: {item['release'].title}")
        do_hide(selected, repo)
        return

    if args.show:
        releases = get_releases(repo, draft=True)
        selected = parse_numbers(args.show, releases)
        if not selected:
            print("有効な番号が見つかりません。")
            return
        for item in selected:
            print(f"再公開対象: {item['release'].title}")
        do_show(selected, repo)
        return

    # 対話モード
    print("エピソード一覧を取得中...")
    releases = get_releases(repo, draft=False)
    if not releases:
        print("公開中のエピソードが見つかりません。")
        return

    print("\n操作を選んでください: 1=削除  2=非公開  3=再公開（非公開から）\n")
    op = input("操作番号: ").strip()

    if op == "1":
        selected = select_by_input(releases, "削除する番号を入力")
        if selected and confirm(selected, "削除"):
            do_delete(selected, repo)
    elif op == "2":
        selected = select_by_input(releases, "非公開にする番号を入力")
        if selected and confirm(selected, "非公開に"):
            do_hide(selected, repo)
    elif op == "3":
        hidden = get_releases(repo, draft=True)
        if not hidden:
            print("非公開のエピソードがありません。")
            return
        selected = select_by_input(hidden, "再公開する番号を入力")
        if selected and confirm(selected, "再公開"):
            do_show(selected, repo)
    else:
        print("キャンセルしました。")


if __name__ == "__main__":
    main()
