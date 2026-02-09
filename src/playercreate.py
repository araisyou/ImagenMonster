import json
from pathlib import Path
from typing import Any, Dict, List

from .chara import Chara
from .item import Item, load_items, items_by_id


def _player_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "Player"


def player_path() -> Path:
    return _player_dir() / "Player.json"


def player_exists() -> bool:
    return player_path().is_file()


def save_player(data: Dict[str, Any]) -> None:
    pdir = _player_dir()
    pdir.mkdir(parents=True, exist_ok=True)
    with player_path().open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_default_player() -> Dict[str, Any]:
    data = {
        "name": "Player",
        "hp": 10,
        "max_hp": 10,
        "attack": 3,
        "defense": 1,
        "agility": 1,
        "skill": ["デモ"],
        "evo": 1,
        "exp": 0,
        "money": 0,
        "image_path": "Player/image/output",
        "feed_items": ["potion", "herb"],
    }
    save_player(data)
    return data


def load_player() -> Dict[str, Any] | None:
    path = player_path()
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_player_chara() -> tuple[Chara, List[Item]] | None:
    data = load_player()
    if data is None:
        return None
    raw_skill = data.get("skill")
    if isinstance(raw_skill, list):
        skills = [str(s) for s in raw_skill if s not in ("", None)]
    elif raw_skill not in ("", None):
        skills = [str(raw_skill)]
    else:
        alt = data.get("skills")
        skills = [str(alt[0])] if isinstance(alt, list) and alt else []
    chara = Chara(
        name=str(data.get("name", "Player")),
        hp=int(data.get("hp", 10)),
        agility=int(data.get("agility", 1)),
        max_hp=int(data.get("max_hp", data.get("hp", 10))),
        attack=int(data.get("attack", 3)),
        defense=int(data.get("defense", 1)),
        skill=skills,
        evo=int(data.get("evo", 1)),
        exp=int(data.get("exp", 0)),
        money=int(data.get("money", 0)),
    )
    feed_item_ids: List[str] = data.get("feed_items", []) or []
    db = items_by_id(load_items())
    feed_items: List[Item] = []
    for fid in feed_item_ids:
        it = db.get(fid)
        if it:
            feed_items.append(it)
    return chara, feed_items


def save_player_state(chara: Chara, feed_items: List[Item]) -> None:
    data = {
        "name": chara.name,
        "hp": chara.hp,
        "max_hp": chara.max_hp,
        "attack": chara.attack,
        "defense": chara.defense,
        "agility": chara.agility,
        "skill": chara.skill,
        "evo": chara.evo,
        "exp": chara.exp,
        "money": chara.money,
        "image_path": str(chara.image_path) if chara.image_path else None,
        "feed_items": [it.id for it in feed_items if it.id],
    }
    save_player(data)


__all__ = [
    "player_path",
    "player_exists",
    "save_player",
    "save_default_player",
    "load_player",
    "load_player_chara",
    "save_player_state",
]
