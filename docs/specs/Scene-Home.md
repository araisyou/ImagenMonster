# Scene/Home.py 仕様

- 役割: ホーム画面の入力処理と状態管理。えさやり/ショップ/ダンジョン遷移を担当。
- 主な処理:
  - 初期化で Player.json またはデフォルトを読み込み、レベル計算し evoを10/20レベル閾値で更新。プレイヤー前面画像をロード。
  - `run()`: イベントループ。えさ/ショップ選択、Enterで実行、Escで終了。
  - `_trigger_option()`: コマンドバー選択に応じてえさモード/ショップ/バトル遷移。
  - `_give_selected_item()`: えさ使用でHP回復、リスト更新、保存。
  - `_confirm_shop()`: 購入処理（所持金チェック、上限6）。
  - `_persist_player()`: 状態保存と evo再計算。
  - `_compute_level()`: exp_table.json または簡易閾値でレベル算出。
  - `_load_player_surface()`: evoに応じて Player/image/output の前面画像を読み込み。
- 入力: キー操作（矢印/WASD/Enter/Esc）。
- 出力: 画面描画（HomeView）。
- 依存: `HomeView`, `BattleCommandUI`, `playercreate`, `load_items`, `Chara`, `_load_skill_defs`。
- 注意: スキルは配列の先頭を表示。skill_infoは skill.json を参照。
