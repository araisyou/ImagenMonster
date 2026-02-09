# Scene/Create.py 仕様

- 役割: プレイヤー初期化と相棒生成フロー（アップロード→生成）。
- 状態: `start` → `upload` → `ready`（選択画像があると生成ボタン活性）。
- 主要UI: タイトル文言、新規開始ボタン「スタート」、画像アップロードボタン、「作成！」ボタン。
- 処理:
  - `save_default_player()` で初期Player.json作成。
  - `_pick_image()`: Tkファイルダイアログで画像を選び Player/image/input/input.png にコピー。
  - `_generate_monster()`: `imagegen()` 呼び出し（例外無視）、出力プレースホルダー画像6枚生成、output.jsonスタブ作成（skill.jsonから先頭3件）。output.jsonの値をPlayer.jsonに統合し、攻撃+5/防御+3/俊敏+3ボーナス付与。
- 入力: マウスクリック、Esc。
- 出力: Player.json/画像出力の更新、on_createdコールバック呼び出し。
- 依存: `playercreate`, `Imagegen.imagegen`, `ui`, `Tk` filedialog, `json`。
- 注意: 例外は多く握りつぶすスタブ挙動。画像が無い場合はプレースホルダーを生成。
