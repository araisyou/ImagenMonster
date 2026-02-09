# feedview.py 仕様

- 役割: ホームの「えさやり」UIを描画。えさリストとステータス、スキル情報表示。
- 主な関数: `draw_feed_mode(surface, font, title_font, feed_items, status, level, skill, skill_info=None, selecting=False, selected_index=0)`。
- 付随: `_lookup_skill(name)` で skill.json を読み込みパワー/コストを取得。
- 入力: `Item` シーケンス、ステータス辞書、レベル、スキル名、選択状態。
- 出力: 描画のみ。
- 依存: `ui.draw_text`, `battlesystem._load_skill_defs`, `Item`。
