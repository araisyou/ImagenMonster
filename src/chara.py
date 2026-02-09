from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import pygame

from .item import Item


@dataclass
class Chara:
    name: str
    hp: int
    attack: int
    defense: int
    agility: int = 1
    max_hp: Optional[int] = None
    skill: List[str] = field(default_factory=list)
    evo: int = 1
    exp: int = 0
    money: int = 0
    image_path: Optional[Path] = None
    items: List[Item] = field(default_factory=list)
    surface: Optional[pygame.Surface] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.max_hp is None:
            self.max_hp = self.hp
        else:
            self.max_hp = max(1, int(self.max_hp))
        self.hp = min(self.hp, self.max_hp)
        if self.image_path:
            self.load_image(self.image_path)

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, dmg: int, ignore_defense: bool = False) -> int:
        # Apply raw damage; defense should already be considered by caller when needed.
        applied = max(0, dmg)
        self.hp = max(0, self.hp - applied)
        return applied

    def heal(self, amount: int) -> int:
        if amount <= 0:
            return 0
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    def load_image(self, path: Path) -> None:
        try:
            img = pygame.image.load(str(path)).convert_alpha()
            self.surface = img
            self.image_path = path
        except (pygame.error, FileNotFoundError):
            self.surface = None

    def set_surface(self, surface: pygame.Surface) -> None:
        self.surface = surface
        self.image_path = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "defense": self.defense,
            "agility": self.agility,
            "skill": self.skill,
            "evo": self.evo,
            "exp": self.exp,
            "money": self.money,
            "items": [self._item_to_dict(it) for it in self.items],
            "image_path": str(self.image_path) if self.image_path else None,
        }

    @staticmethod
    def _item_to_dict(item: Item) -> dict:
        return {
            "name": item.name,
            "price": item.price,
            "heal": item.heal,
            "image_path": str(item.image_path) if item.image_path else None,
        }


__all__ = ["Chara"]
