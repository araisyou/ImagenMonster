# ImagenMonsters

画像から相棒モンスターを作り、育て、バトルするpygameゲームです。

## 必要環境
- Python 3.10 以上
- Windows（動作確認済み）

依存関係のインストール（仮想環境を使う場合は有効化してから）:
```bash
pip install -r requirements.txt
```

## 起動方法
プロジェクトルートで実行:
```bash
python main.py
```
- タイトル: assets/Title.png を背景に使用。Enterで開始。
- ホーム: 相棒表示。evo 1/2/3で larva/adult/final のスプライト（Player/image/output）を使用。
- 作成: プレイヤー初期化→画像アップロード→「作成！」でプレースホルダー生成とステータス統合（攻撃+5、防御+3、俊敏+3）を実行。
- バトル: プレイヤーはevoに応じた背面スプライト、敵は assets/enemy/enemy.json の image_path を使用。

## データファイル
- Player/Player.json: 現在のプレイヤー情報。
- Player/output.json: 生成結果。Player.jsonに統合。
- Player/exp_table.json: 経験値テーブル（最大30レベル対応）。
- Player/skill.json: スキル定義。
- assets/enemy/enemy.json: 敵ステータスと画像パス。
- assets/Title.png: タイトル背景。

## 操作方法
- タイトル: Enterで開始。
- ホーム: 矢印/WASDで選択、Enter/Space決定、Esc戻る。
- 作成: ボタンで開始/アップロード/作成、Esc終了。
- バトル: 矢印でターゲット選択、Enter/Spaceで決定、Esc終了。

## 注意
- 相棒スプライト（front/back）は Player/image/output に larva_front/back, adult_front/back, final_front/back を配置。
- 敵画像は enemy.json が参照する assets/enemy/image 配下に配置してください。
