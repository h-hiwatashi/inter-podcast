# タスク一覧

## フェーズ1: リポジトリ・インフラ準備

- [x] GitHubリポジトリ作成 (`h-hiwatashi/inter-podcast`)
- [x] プロジェクト初期ファイル作成・push
- [x] `design.md` 作成・push
- [x] GitHub Pages 有効化（Settings > Pages > Branch: main / root）
- [ ] GitHub Secrets 設定
  - [ ] `ANTHROPIC_API_KEY`
  - [ ] `GOOGLE_APPLICATION_CREDENTIALS_JSON`

---

## フェーズ2: Google Cloud 設定

- [x] Google Cloud プロジェクト作成
- [x] Text-to-Speech API 有効化
- [x] サービスアカウント作成（ロール: Cloud Text-to-Speech API User）
- [x] サービスアカウントキー（JSON）のダウンロード

---

## フェーズ3: ローカル動作確認

- [ ] Python 仮想環境作成・依存パッケージインストール (`pip install -r requirements.txt`)
- [ ] 環境変数設定（`ANTHROPIC_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`, `GITHUB_TOKEN`, `GITHUB_REPOSITORY`）
- [ ] `fetcher.py` 単体確認（RSS取得・記事表示）
- [ ] `translator.py` 単体確認（台本生成・内容確認）
- [ ] `tts.py` 単体確認（MP3ファイル生成・再生確認）
- [ ] `publisher.py` 単体確認（GitHub Release作成・feed.xml 更新）
- [ ] `main.py` 通し実行（全工程エンドツーエンド確認）

---

## フェーズ4: GitHub Actions 確認

- [ ] `workflow_dispatch` で手動トリガー実行
- [ ] Actions ログでエラーがないこと確認
- [ ] GitHub Releases に MP3 がアップロードされていること確認
- [ ] `feed.xml` が更新されてpushされていること確認
- [ ] `processed_urls.json` が更新されてpushされていること確認

---

## フェーズ5: Spotify 登録

- [ ] Spotify for Podcasters アカウント作成
- [ ] GitHub Pages の feed.xml URL を確認（`https://h-hiwatashi.github.io/inter-podcast/feed.xml`）
- [ ] Spotify for Podcasters に RSS URL でポッドキャスト登録
- [ ] Spotify 側でエピソードが表示されること確認

---

## フェーズ6: 品質調整（動作確認後）

- [ ] 台本の品質確認（翻訳精度・読み上げ調の自然さ）
- [ ] TTS音声の確認（速度・音質）
- [ ] 1エピソードあたりの長さ確認（目標: 3〜5分）
- [ ] 必要に応じて `translator.py` のプロンプト調整
- [ ] 必要に応じて `tts.py` の `speaking_rate` / `pitch` 調整
- [ ] ポッドキャスト番組名・説明文の最終決定・`config.py` 更新
- [ ] カバー画像（`cover.jpg`）作成・リポジトリに追加

---

## フェーズ7: 安定運用（長期）

- [ ] cron スケジュールの動作確認（自動実行ログ確認）
- [ ] 新記事0件時の早期終了が正常に動作すること確認
- [ ] エラー時の通知設定（GitHub Actions の失敗メール or Slack 通知）
- [ ] 定期的な feed.xml のバリデーション確認
