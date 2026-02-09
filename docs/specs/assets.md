# assets.py 仕様

- 役割: 画像を読み込み、指定サイズ内に収まるようアスペクト比を維持して縮小するユーティリティ。
- 主な関数: `load_image(path, max_size)` 画像が存在しない場合はパネル色のプレースホルダーを返す。
- 入力: 画像パス、最大サイズ(tuple[int,int])。
- 出力: 縮小済み `pygame.Surface`。
- 依存: `pygame`, `constants.PANEL_COLOR`。
- 注意: 拡大は行わず、存在しない場合はクロスマーク付きプレースホルダーを生成。
