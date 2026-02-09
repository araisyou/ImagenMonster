from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict


@dataclass
class Item:
    id: str
    name: str
    price: int
    heal: int
    image_path: Optional[Path] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            price=int(data.get("price", 0)),
            heal=int(data.get("heal", 0)),
            image_path=Path(data["image_path"]) if data.get("image_path") else None,
        )


def default_items_path() -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / "item" / "items.json"


def load_items(path: Optional[Path] = None) -> List[Item]:
    p = path or default_items_path()
    if not p.is_file():
        return []
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        return [Item.from_dict(d) for d in data]
    except (json.JSONDecodeError, OSError, ValueError):
        return []


def items_by_id(items: List[Item]) -> Dict[str, Item]:
    return {it.id: it for it in items if it.id}


__all__ = ["Item", "load_items", "default_items_path", "items_by_id"]
