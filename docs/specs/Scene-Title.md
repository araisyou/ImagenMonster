# Scene/Title.py 仕様

- 役割: タイトル画面。背景画像を表示しEnter開始を受け付ける。
- UI: assets/Title.png をウィンドウサイズにスケーリングして表示。画面下部に「エンターキーではじめる」テキスト。
- 入力: Enter/テンキーEnterでゲーム開始、QUITで終了。
- 処理: 背景読み込み失敗時は単色背景。
- 依存: `ui.fill_background/draw_text`, `constants`, `Path`。
