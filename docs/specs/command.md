# command.py 仕様

- 役割: コマンドUIの描画と選択管理。
- 主なクラス: `BattleCommandUI`
  - `handle_event(event)`: 左右キー/WASDで選択移動。
  - `draw(surface, font)`: 下部バーに選択中ラベルを描画。
  - `current_option()`, `set_options(options)`。
- ヘルパー: `layout_button_row`, `draw_button_row` ボタン行の配置/クリック判定。
- 入力: pygameイベント、マウス情報。
- 出力: クリックインデックスや選択中ラベル。
- 依存: `ui.draw_button`, `constants`。
