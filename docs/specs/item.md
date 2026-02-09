# item.py 仕様

- 役割: アイテムデータモデルと読み込みユーティリティ。
- 主な要素:
  - クラス `Item(id, name, price, heal, image_path)`。
  - `from_dict`, `default_items_path`, `load_items(path=None)`, `items_by_id(items)`。
- 入力: assets/item/items.json（デフォルト）。
- 出力: `Item` リスト、ID→Itemマップ。
- 注意: JSONが無い/不正でも空リストを返す。image_pathは `Path` に変換。
