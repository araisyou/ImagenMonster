# Imagegen.py 仕様

- 役割: 画像生成/解析フロー（Gemini API利用前提のスタブ実装）。キーワード抽出、ステータス配分、デザイン仕様、画像生成などを担う想定。
- 主な要素:
  - Pydanticモデル: `KeywordResult`, `StatAddResult`, `DesignSpec`。
  - ユーティリティ: `ensure_dir`, `require_file`, `strip_code_fences`, 画像Part変換/保存関数。
  - ステップ関数: `analyze_image_keywords`, `validate_and_fix_add`, ほか生成系（ファイル全体に多数）。
- 入出力: `Player/skill.json`, `Player/image/input/input.png` を入力に、`Player/image/output/*` と `Player/output.json` を出力する設計。
- 依存: `google.genai`, `PIL`, `dotenv` など（requirements参照）。
- 注意: 現状ゲーム内では Create シーンで `imagegen()` を呼ぶが例外は握りつぶし。APIキーが必要。詳細手順はコード内コメント参照。
