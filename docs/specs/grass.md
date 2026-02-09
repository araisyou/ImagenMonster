# grass.py 仕様

- 役割: ホーム画面で使う地面のみの疑似3Dレンダラー。
- 主なクラス: `Grass`
  - `draw(surface, time_sec=0.0)`: チェッカー地面をスライスで描画。
- 特徴: corridorの床部分を簡略化。テクスチャが無い場合は緑チェックを生成。
- 入力: 描画先Surfaceと経過時間。
- 出力: 描画のみ。
- 依存: `pygame`, `constants`, `assets/texture/grass.png`（任意）。
