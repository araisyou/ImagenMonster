# Scene/Test.py 仕様

- 役割: assets/images ビューアと簡易Gemini要約生成テスト。
- UI: 前/次/参照ボタン、左に画像、右にメタ情報表示。
- 処理:
  - `_load_assets_images()`: assets/images の画像を読み込み、image_to_textでJSON生成、テキスト読込。
  - `_draw_layout()`: 現在の画像と情報、ボタンを描画。
  - `_choose_and_add_image()`: ファイルダイアログから画像を追加コピーし、連番命名して登録。
- 入力: マウスクリック、QUIT。
- 依存: `assets.load_image`, `ImageToText.image_to_text`, `read_text_from_json`, `ui`, `Tk`。
- 注意: assets/images が無い場合はメッセージ表示のみ。Geminiキーが無い場合は簡易情報のみ。
