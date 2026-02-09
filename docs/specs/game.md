# game.py 仕様

- 役割: アプリのエントリーポイント。pygame初期化、フォント設定、シーン遷移管理。
- 主なクラス: `Game`
  - `run()`: 現在のシーンを実行し終了でpygame終了。
  - `_on_game()`: プレイヤーデータ有無でHome/ Createに遷移。
  - `_start_home()`, `_start_battle()`, `_start_create()`, `_on_ai()`: 各シーン起動。
- 入力: なし（実行時にシーンイベントを処理）。
- 出力: なし（シーン描画）。
- 依存: `constants`, 各Sceneモジュール, `playercreate`。
- 注意: ウィンドウサイズは constants に準拠。Battle後HP/お金が0ならGameOverからTitleへ戻る。
