# ui.py 仕様

- 役割: 共通UI描画ユーティリティ。
- 主な関数:
  - `fill_background(surface)`: 背景塗りつぶし。
  - `draw_panel(surface, rect)`: パネル枠描画。
  - `draw_text(surface, text, pos, font, color=TEXT_COLOR)`: テキスト描画。
  - `draw_button(surface, rect, text, font, mouse_pos, mouse_down)`: ボタン描画とクリック判定。
- 入力: `pygame.Surface`, 位置/矩形、マウス状態。
- 出力: 描画、ボタンはクリック可否をboolで返す。
- 依存: `constants` 色設定。
