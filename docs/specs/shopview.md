# shopview.py 仕様

- 役割: ホーム内ショップUIの描画。
- 主な関数: `draw_shop(surface, font, title_font, items, selecting=True, selected_index=0, money=0)`。
- 表示: 左に商品リスト、右に詳細（名前/価格/回復量/画像パス）を表示。所持金表示付き。
- 入力: `Item` リスト、選択状態、所持金。
- 出力: 描画のみ。
- 依存: `ui.draw_text`, `Item`。
