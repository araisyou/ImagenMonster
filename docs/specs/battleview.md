# battleview.py 仕様

- 役割: 戦闘シーンでプレイヤーと最大3体の敵を描画。
- 主なクラス: `BattleView`
  - `set_player(surface)`: プレイヤー画像設定。
  - `set_enemy_charas(charas)`: 敵 `Chara` から画像をロードし内部保持。
  - `draw(surface, enemy_alphas=None)`: 透明度を考慮して描画。
  - `enemy_rects(count)`: 敵配置矩形計算。
- 補助関数: `draw_stage_cutin`, `draw_stage_clear` で演出オーバーレイ。
- 入力: `pygame.Surface` 群、敵アルファ値リスト（任意）。
- 出力: 描画のみ（値は返さない）。
- 依存: `pygame`, `Chara`, `constants`。
- 注意: プレイヤーは前面180x180、敵は後列80x120。画像が無い場合は色付きプレースホルダー。
