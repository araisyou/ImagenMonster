# battlesystem.py 仕様

- 役割: 戦闘ロジック本体。敵出現、行動順、攻撃処理、経験値・報酬集計を管理。
- 主な型/関数:
  - `BattleSystem`: コンストラクタで各種コールバック（プレイヤー行動、敵撃破、ステージ開始、攻撃演出）を受け取り、`run()` でステージ進行。
  - `_load_enemy_defs()`, `_fallback_enemy_defs()`: 敵定義の読み込み/フォールバック。
  - `_load_skill_defs()`: プレイヤースキル定義読み込み。
  - `_enemy_to_chara()`, `_unique_enemies()`: 敵プロトから `Chara` を生成（`image_path` をプロジェクトルート相対で解決）。
- 入力: `assets/enemy/enemy.json` の敵リスト、`Player/skill.json`、`Player/Player.json`（プレイヤー）。
- 出力: `run()` の結果ディクショナリ（result/stage/kills/exp/money/hp）。
- 依存: `Chara`, `playercreate.load_player_chara`, `random`。
- 注意: 敵画像は相対パスをプロジェクトルートで解決。スキル定義が無い場合は空ディクショナリ。
