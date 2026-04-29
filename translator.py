import anthropic
from config import CLAUDE_MODEL, ANTHROPIC_API_KEY


def generate_script(articles: list[dict]) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    articles_text = ""
    for i, article in enumerate(articles, 1):
        articles_text += f"""
【記事{i}】
タイトル: {article['title']}
内容: {article['summary']}
URL: {article['url']}
"""

    prompt = f"""あなたはインテルミラノの日本語ポッドキャストのナレーターです。
以下のイタリア語ニュース記事を日本語に翻訳し、ラジオニュース風の台本を作成してください。

要件:
- 冒頭に「こんにちは、インテルミラノニュース速報です。」で始める
- 各ニュースをニュース読み上げ調で簡潔に伝える（話し言葉、です・ます調）
- 記事間は「続いて」「次のニュースです」などで自然につなぐ
- 末尾は「以上、インテルミラノニュース速報でした。」で締める
- 固有名詞（選手名・チーム名）はカタカナ表記
- 音声読み上げ用なので記号や箇条書きは使わない
- 全体で6〜8分程度（約2000〜2500文字）に収める
- 以下の選手名・監督名は必ず指定の読み仮名カタカナで表記すること:
  【監督】
  Cristian Chivu → クリスティアン・キブ
  【GK】
  Yann Sommer → ヤン・ゾマー
  Josep Martínez Riera → ジョゼップ・マルティネス
  Raffaele Di Gennaro → ラッファエーレ・ディ・ジェンナーロ
  Alessandro Calligaris → アレッサンドロ・カッリガリス
  【DF】
  Alessandro Bastoni → アレッサンドロ・バストーニ
  Stefan de Vrij → ステファン・デ・フライ
  Francesco Acerbi → フランチェスコ・アチェルビ
  Carlos Augusto → カルロス・アウグスト
  Manuel Akanji → マニュエル・アカンジ
  Yann Bisseck → ヤン・ビセック
  Federico Dimarco → フェデリコ・ディマルコ
  Denzel Dumfries → デンゼル・ダンフリース
  【MF】
  Nicolò Barella → ニコロ・バレッラ
  Hakan Çalhanoğlu → ハカン・チャルハノール
  Henrikh Mkhitaryan → ヘンリク・ムヒタリャン
  Davide Frattesi → ダヴィデ・フラッテージ
  Piotr Zieliński → ピョトル・ジエリンスキ
  Andy Diouf → アンディ・ジウフ
  Petar Sučić → ペタル・スチッチ
  【FW】
  Lautaro Martínez → ラウタロ・マルティネス
  Marcus Thuram → マルクス・テュラム
  Francesco Pio Esposito → フランチェスコ・ピオ・エスポジト
  Ange-Yoan Bonny → アンジュ＝ヨアン・ボニー
  Luis Henrique → ルイス・エンリケ

ニュース記事:
{articles_text}

台本のみを出力してください。前置きや説明は不要です。"""

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text
