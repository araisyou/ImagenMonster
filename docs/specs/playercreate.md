# playercreate.py 仕様

- 役割: プレイヤーデータ(Player.json)の作成・読み書き・Chara変換。
- 主な関数:
  - `player_path()`, `player_exists()`, `_player_dir()`。
  - `save_player(data)`, `save_default_player()`：初期データには skill配列・evo・feed_items初期値を含む。
  - `load_player()`: Player.json読込。
  - `load_player_chara()`: Player.jsonから `Chara` と所持えさ(`Item` リスト)を構築。
  - `save_player_state(chara, feed_items)`: 現在の状態を保存。
- 入力/出力: Player/Player.json。アイテムは assets/item/items.json を参照。
- 注意: skillは配列として扱う。データ欠損時はデフォルト値補正。
