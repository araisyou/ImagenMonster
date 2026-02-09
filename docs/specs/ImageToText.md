# ImageToText.py 仕様

- 役割: 画像メタ情報とGemini要約を生成し JSON に保存。
- 主な関数:
  - `image_to_text(image_path, api_key=None)`: 既存JSONがあればスキップ。サイズ/平均色/Gemini要約を assets/imagetotext/*.json に出力。
  - `read_text_from_json(image_path)`: 生成済みJSONを読み込み。
- 入力: 画像パス、環境変数 `GEMINI_API_KEY`（任意）。
- 出力: JSONファイルに文字列リスト。
- 依存: `pygame`, `google-generativeai`（任意）、`mimetypes`。
- 注意: APIキー未設定やライブラリ未導入時は簡易情報のみ書き込む。例外はなるべく抑制。
