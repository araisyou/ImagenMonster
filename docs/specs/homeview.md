# homeview.py 仕様

- 役割: ホームシーンの描画（地面、プレイヤー、えさ/ショップUI、メッセージ）。
- 主なクラス: `HomeView`
  - `draw_player(surface, sprite=None, alpha=1.0)`: プレイヤー画像またはプレースホルダーを表示。
  - `draw(...)`: grass描画、プレイヤー表示、feed/shop UI、コマンドバー、中央メッセージ。
- 入力: `feed_items`, `status`, `level`, `skill`, `skill_info`, `player_surface`, `shop_items` など表示データ。
- 出力: 描画のみ。
- 依存: `Grass`, `feedview.draw_feed_mode`, `shopview.draw_shop`, `ui.draw_text`, `constants`。
