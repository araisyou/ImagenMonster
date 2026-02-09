# Scene/Battle.py 仕様

- 役割: バトルシーンの入出力と演出。BattleSystemを駆動し、UI/描画/入力を扱う。
- 主なフロー:
  - `run()`: player/feed_items読み込み→BattleSystem実行→結果オーバーレイ表示。
  - `_player_action`: コマンド選択（たたかう/にげる→攻撃/防御/スキル）、ターゲット選択。
  - `_on_stage_start`, `_on_enemy_defeated`, `_on_player_attack`, `_on_enemy_attack`: 各演出描画。
  - `_draw_player_choice`: コリドー背景＋BattleViewでプレイヤー（evo別背面）/敵表示、HUD描画。
- データ: プレイヤーは `load_player_chara` から取得し、evoに応じた背面画像を `Player/image/output/*_back.png` からロード。
- 入力: キー入力（矢印/WASD/Enter/Esc）。
- 出力: 描画のみ。結果は `BattleSystem.run()` の戻りに応じてGame/GameOverへ引き継ぎ。
- 依存: `BattleSystem`, `BattleView`, `Corridor`, `BattleCommandUI`, `playercreate`, `constants`。
- 注意: 逃走は結果`escape`。防御選択時は防御力を一時2倍。
