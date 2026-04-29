import os

RSS_FEED_URL = "https://fcinter1908.it/feed/"
CLAUDE_MODEL = "claude-sonnet-4-6"
TTS_VOICE = "ja-JP-Neural2-B"
MAX_ARTICLES_PER_EPISODE = 10

PODCAST_TITLE = "インテルミラノ ニュース速報"
PODCAST_DESCRIPTION = "イタリアのインテルミラノ最新ニュースを日本語でお届けするポッドキャストです。"
PODCAST_LANGUAGE = "ja"
PODCAST_AUTHOR = "Inter Podcast Bot"

GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY", "h-hiwatashi/inter-podcast")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

PROCESSED_URLS_FILE = "processed_urls.json"
FEED_FILE = "feed.xml"
MAX_FEED_EPISODES = 30
