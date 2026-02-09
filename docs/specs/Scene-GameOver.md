# Scene/GameOver.py 仕様

- 役割: ゲームオーバー画面の表示とプレイヤーデータ削除。
- 処理: Enter/Space/Returnで終了。描画は簡易テキストのみ。
- 終了時: Player/Player.json を削除（存在時）。
- 依存: `playercreate.player_path`, `ui.draw_text`, `constants`。
- 入力: キーイベント、QUIT。
