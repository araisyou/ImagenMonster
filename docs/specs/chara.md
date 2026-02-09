# chara.py 仕様

- 役割: プレイヤー/敵キャラクターのデータモデル。
- 主なクラス: `Chara`
  - 属性: `name, hp, max_hp, attack, defense, agility, skill(list), evo, exp, money, image_path, items`。
  - `__post_init__`: max_hp補正、画像ロード。
  - `is_alive()`, `take_damage()`, `heal()`, `load_image()`, `set_surface()`, `to_dict()`。
- 入出力: 数値ステータスと画像パスを保持、各メソッドは状態更新。
- 依存: `pygame`（画像ロード）、`Item`。
- 注意: `take_damage` は防御を考慮しない前提で呼び出し側が補正。`surface` は直列化しない。
