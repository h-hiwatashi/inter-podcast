# Inter Milan 日本語ポッドキャスト — 設計ドキュメント

## プロジェクト概要

イタリア語メディアのインテルミラノ関連ニュースを自動取得し、日本語音声に変換してポッドキャストとして配信する完全自動化パイプライン。

- **配信頻度**: 1日2回（JST 朝6時・夕18時）
- **言語**: イタリア語ニュース → 日本語台本 → 日本語音声
- **配信先**: Spotify for Podcasters

---

## 技術スタック

| 役割 | 技術 | 備考 |
|---|---|---|
| 言語 | Python 3.12 | |
| ニュース取得 | RSS フィード (`feedparser`) | fcinter1908.it/feed/ |
| 翻訳・台本生成 | Claude API (`claude-sonnet-4-20250514`) | 月数百円程度 |
| 音声合成 | Google Cloud Text-to-Speech API | `ja-JP-Neural2-B`、月100万文字まで無料 |
| 実行環境 | GitHub Actions | 無料、cronで1日2回 |
| MP3ホスティング | GitHub Releases | 1ファイル2GBまで無料 |
| RSS配信 | GitHub Pages | `feed.xml` を静的ホスティング |
| Podcast配信 | Spotify for Podcasters | 無料 |

---

## プロジェクト構成

```
inter-podcast/
├── main.py                       # エントリーポイント（全体を統括）
├── fetcher.py                    # RSSからニュース取得・重複排除
├── translator.py                 # Claude APIで翻訳・台本生成
├── tts.py                        # Google Cloud TTSで音声生成
├── publisher.py                  # GitHub Releases upload + RSS更新
├── config.py                     # 設定値まとめ
├── processed_urls.json           # 処理済み記事URL管理（gitで永続化）
├── feed.xml                      # Podcast RSS（GitHub Pagesで配信）
├── .github/
│   └── workflows/
│       └── podcast.yml           # GitHub Actions（1日2回実行）
└── requirements.txt
```

---

## パイプライン全体フロー

```
[GitHub Actions cron]
        │
        ▼
  fetcher.py
  ┌─────────────────────────────────────┐
  │ RSSフェッチ (fcinter1908.it/feed/)  │
  │ processed_urls.json で重複排除      │
  │ 最大5件の新着記事を返す             │
  └─────────────────────────────────────┘
        │ 新記事あり
        ▼
  translator.py
  ┌─────────────────────────────────────┐
  │ Claude API に5記事を一括送信        │
  │ イタリア語→日本語翻訳              │
  │ ニュース読み上げ調の台本生成        │
  │ （約1000〜1500文字）               │
  └─────────────────────────────────────┘
        │
        ▼
  tts.py
  ┌─────────────────────────────────────┐
  │ Google Cloud TTS で MP3 生成        │
  │ 音声: ja-JP-Neural2-B              │
  └─────────────────────────────────────┘
        │
        ▼
  publisher.py
  ┌─────────────────────────────────────┐
  │ GitHub Releases に MP3 アップロード │
  │ feed.xml に新エピソードを追記       │
  │ （最新30件を保持）                  │
  └─────────────────────────────────────┘
        │
        ▼
  main.py（後処理）
  ┌─────────────────────────────────────┐
  │ processed_urls.json を更新          │
  │ feed.xml + processed_urls.json を   │
  │ git commit & push                   │
  └─────────────────────────────────────┘
        │
        ▼
  [Spotify for Podcasters]
  GitHub Pages の feed.xml を購読
```

---

## 各モジュール詳細

### config.py
全モジュールで共有する定数・環境変数を一元管理。

| 定数 | 値 | 説明 |
|---|---|---|
| `RSS_FEED_URL` | `https://fcinter1908.it/feed/` | ニュースソース |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | 使用するClaudeモデル |
| `TTS_VOICE` | `ja-JP-Neural2-B` | Google TTS音声 |
| `MAX_ARTICLES_PER_EPISODE` | 5 | 1エピソードあたりの記事数 |
| `MAX_FEED_EPISODES` | 30 | feed.xmlに保持するエピソード数 |

### fetcher.py
- `feedparser` でRSSフェッチ
- `processed_urls.json` と照合して未処理記事のみ抽出
- 新記事0件の場合は早期終了（後続処理をスキップ）
- 各記事: `{title, summary, url, published}` の辞書形式

### translator.py
- 5記事を**1回のAPIコール**にまとめて送信（コスト最適化）
- プロンプト要件:
  - 冒頭: 「こんにちは、インテルミラノニュース速報です。」
  - 各記事: ニュース読み上げ調（簡潔・客観的・です/ます調）
  - 記事間: 「続いて」「次のニュースです」で自然につなぐ
  - 末尾: 「以上、インテルミラノニュース速報でした。」
  - 固有名詞はカタカナ表記、記号・箇条書き不使用（TTS向け）

### tts.py
- `google-cloud-texttospeech` ライブラリ使用
- 音声: `ja-JP-Neural2-B`（自然な男性声、Neural2シリーズ）
- エンコード: MP3
- 環境変数 `GOOGLE_APPLICATION_CREDENTIALS` でサービスアカウント認証

### publisher.py
- **GitHub Releases**: `PyGithub` でリリース作成 → MP3をアセットとしてアップロード
- **feed.xml更新**: `lxml` でXML操作、Podcast RSS 2.0形式
  - `<itunes:*>` 名前空間でSpotify/Apple Podcast互換
  - 新エピソードを先頭に挿入（新しい順）
  - 最大30件を超えたら古いものを削除

### main.py
エラー時は非ゼロ終了（GitHub Actionsが失敗として記録）。

```
fetch → translate → tts → upload → update_feed → commit
```

### podcast.yml (GitHub Actions)
```yaml
on:
  schedule:
    - cron: '0 21 * * *'   # JST 朝6時 (UTC 21時)
    - cron: '0 9 * * *'    # JST 夕18時 (UTC 9時)
  workflow_dispatch:         # 手動実行（テスト用）

permissions:
  contents: write            # feed.xml / processed_urls.json をpush
```

---

## 状態管理の設計

### 重複排除
- 処理済み記事URLを `processed_urls.json`（配列）にリポジトリとして管理
- GitHub ActionsがGITHUB_TOKENで自動コミット・push
- キャッシュやDBを使わないためシンプルで障害に強い

### RSS配信
- `feed.xml` をリポジトリに直接コミット
- GitHub Pagesで `https://h-hiwatashi.github.io/inter-podcast/feed.xml` として公開
- Spotify for PodcastersにこのURLを登録

---

## 必要なAPIキー・認証情報

| キー | 取得場所 | GitHub Secretsの変数名 |
|---|---|---|
| Claude API Key | console.anthropic.com | `ANTHROPIC_API_KEY` |
| Google Cloud 認証JSON | Google Cloud Console | `GOOGLE_APPLICATION_CREDENTIALS_JSON` |

`GITHUB_TOKEN` はGitHub Actionsが自動提供。

---

## セットアップ手順

1. **GitHub Pages有効化**
   Settings > Pages > Source: Deploy from branch > Branch: `main` / `/ (root)`

2. **GitHub Secrets設定**
   Settings > Secrets and variables > Actions
   - `ANTHROPIC_API_KEY`
   - `GOOGLE_APPLICATION_CREDENTIALS_JSON`（サービスアカウントJSONをそのまま貼り付け）

3. **Google Cloud設定**
   - プロジェクト作成
   - Text-to-Speech API 有効化
   - サービスアカウント作成（ロール: Cloud Text-to-Speech API User）
   - サービスアカウントキー（JSON）をダウンロード

4. **Spotify for Podcasters登録**
   - podcasters.spotify.com でアカウント作成
   - 「RSS URLでインポート」から feed.xml のURLを登録

---

## ローカル動作確認

```bash
# 依存パッケージインストール
pip install -r requirements.txt

# 環境変数設定
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-key.json
export GITHUB_TOKEN=ghp_...
export GITHUB_REPOSITORY=h-hiwatashi/inter-podcast

# 実行
python main.py
```

---

## コスト見積もり

| サービス | 無料枠 | 想定使用量 | 月額コスト |
|---|---|---|---|
| Claude API | なし | 約60エピソード × ~2000トークン | 数百円 |
| Google Cloud TTS | 100万文字/月 | 約60 × 1500文字 = 9万文字 | 無料 |
| GitHub Actions | 2000分/月（public無制限） | パブリックリポジトリのため無制限 | 無料 |
| GitHub Releases | 容量制限あり（2GB/ファイル） | MP3 数MB/本 | 無料 |
| GitHub Pages | 無制限 | feed.xml のみ | 無料 |
| Spotify for Podcasters | 無制限 | — | 無料 |

**合計: Claude API代のみ（月数百円）**
