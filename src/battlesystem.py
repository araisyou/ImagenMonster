import json
import random
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Tuple, Union

from .chara import Chara
from .playercreate import load_player_chara, save_default_player

# Type alias for a player action callback: given the player and a list of alive enemies,
# returns either target index (int), a tuple (index, action_type), or None for escape.
PlayerAction = Callable[[Chara, List[Chara]], Optional[Union[int, Tuple[int, str]]]]
EnemyDefeatCallback = Callable[[Chara, List[Chara], Chara], None]
StageStartCallback = Callable[[List[Chara], int], None]
PlayerAttackCallback = Callable[[Chara, Chara, int, List[Chara]], None]
EnemyAttackCallback = Callable[[Chara, Chara, int], None]


def _load_enemy_defs() -> List[dict]:
    path = Path(__file__).resolve().parents[1] / "assets" / "enemy" / "enemy.json"
    if not path.is_file():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = f.read()
            if not data.strip():
                return []
            return json.loads(data) or []
    except json.JSONDecodeError:
        # broken file; fail soft
        return []


def _fallback_enemy_defs() -> List[dict]:
    # Simple default so battle can proceed even if file missing/invalid
    return [
        {"name": "Slime", "hp": 8, "max_hp": 8, "attack": 2, "defense": 0, "agility": 1, "skill": None, "exp": 10, "money": 5},
        {"name": "Bat", "hp": 6, "max_hp": 6, "attack": 3, "defense": 0, "agility": 2, "skill": None, "exp": 12, "money": 6},
    ]


def _load_skill_defs() -> dict:
    path = Path(__file__).resolve().parents[1] / "Player" / "skill.json"
    if not path.is_file():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _enemy_to_chara(proto: dict, suffix: Optional[int] = None) -> Chara:
    name = str(proto.get("name", "Enemy"))
    if suffix is not None:
        name = f"{name}{suffix}"
    hp = int(proto.get("hp", 1))
    max_hp = int(proto.get("max_hp", hp))
    atk = int(proto.get("attack", 1))
    deff = int(proto.get("defense", 0))
    agi = int(proto.get("agility", 1))
    skill = proto.get("skill")
    exp = int(proto.get("exp", 0))
    money = int(proto.get("money", 0))
    image_path = proto.get("image_path")
    img_path = None
    if image_path:
        img_path = Path(image_path)
        if not img_path.is_absolute():
            img_path = Path(__file__).resolve().parents[1] / img_path
    return Chara(name=name, hp=hp, max_hp=max_hp, attack=atk, defense=deff, agility=agi, skill=skill, exp=exp, money=money, image_path=img_path)


def _unique_enemies(protos: Sequence[dict], count: int) -> List[Chara]:
    picked: List[dict] = [random.choice(protos) for _ in range(count)]
    name_counts: dict[str, int] = {}
    result: List[Chara] = []
    for proto in picked:
        base_name = str(proto.get("name", "Enemy"))
        name_counts[base_name] = name_counts.get(base_name, 0) + 1
        suffix = name_counts[base_name] if name_counts[base_name] > 1 else None
        result.append(_enemy_to_chara(proto, suffix))
    return result


class BattleSystem:
    """Turn-based battle loop driven by agility.

    Usage:
        system = BattleSystem(max_stage=3)
        result = system.run()
    """

    def __init__(
        self,
        max_stage: int = 3,
        player_action: Optional[PlayerAction] = None,
        on_enemy_defeated: Optional[EnemyDefeatCallback] = None,
        on_stage_start: Optional[StageStartCallback] = None,
        on_player_attack: Optional[PlayerAttackCallback] = None,
        on_enemy_attack: Optional[EnemyAttackCallback] = None,
    ) -> None:
        self.max_stage = max_stage
        self.player_action = player_action or self._default_player_action
        self.enemy_defs = _load_enemy_defs() or _fallback_enemy_defs()
        self.player = self._load_player()
        self.on_enemy_defeated = on_enemy_defeated
        self.on_stage_start = on_stage_start
        self.on_player_attack = on_player_attack
        self.on_enemy_attack = on_enemy_attack
        self.skill_defs = _load_skill_defs()
        self.total_exp = 0
        self.total_money = 0
        self.total_kills = 0

    def _load_player(self) -> Chara:
        bundle = load_player_chara()
        if bundle is None:
            save_default_player()
            bundle = load_player_chara()
        if bundle is None:
            # ultimate fallback
            return Chara(name="Player", hp=10, max_hp=10, attack=3, defense=1, agility=1)
        chara, _ = bundle
        return chara

    def run(self) -> dict:
        stage = 1
        while stage <= self.max_stage:
            if not self.player.is_alive():
                return {
                    "result": "defeat",
                    "stage": stage,
                    "kills": self.total_kills,
                    "exp": self.total_exp,
                    "money": self.total_money,
                    "hp": self.player.hp,
                }
            enemies = self._spawn_enemies()
            if self.on_stage_start:
                self.on_stage_start(enemies, stage)
            outcome = self._battle_stage(enemies)
            if outcome == "escape":
                return {
                    "result": "escape",
                    "stage": stage,
                    "kills": self.total_kills,
                    "exp": self.total_exp,
                    "money": self.total_money,
                    "hp": self.player.hp,
                }
            if outcome == "defeat":
                return {
                    "result": "defeat",
                    "stage": stage,
                    "kills": self.total_kills,
                    "exp": self.total_exp,
                    "money": self.total_money,
                    "hp": self.player.hp,
                }
            stage += 1
        return {
            "result": "victory",
            "stage": self.max_stage,
            "kills": self.total_kills,
            "exp": self.total_exp,
            "money": self.total_money,
            "hp": self.player.hp,
        }

    def _spawn_enemies(self) -> List[Chara]:
        if not self.enemy_defs:
            return []
        count = random.randint(1, 3)
        return _unique_enemies(self.enemy_defs, count)

    def _turn_order(self, actors: List[Chara]) -> List[Chara]:
        # sort by agility desc, then stable by list order
        return sorted(actors, key=lambda c: c.agility, reverse=True)

    def _battle_stage(self, enemies: List[Chara]) -> str:
        actors: List[Chara] = [self.player] + enemies
        while self.player.is_alive() and any(e.is_alive() for e in enemies):
            for actor in self._turn_order(actors):
                if not actor.is_alive():
                    continue
                if actor is self.player:
                    alive_enemies = [e for e in enemies if e.is_alive()]
                    if not alive_enemies:
                        break
                    action = self.player_action(self.player, alive_enemies)
                    if action is None:
                        return "escape"
                    action_type = "attack"
                    target_idx = action
                    if isinstance(action, tuple) and len(action) >= 2:
                        target_idx, action_type = action[0], str(action[1])
                    if target_idx == -2:
                        continue  # guard: no attack
                    if target_idx < 0:
                        return "escape"
                    if target_idx >= len(alive_enemies):
                        target_idx = 0
                    target = alive_enemies[target_idx]
                    active_skill = self._active_skill_name(getattr(self.player, "skill", None))
                    if action_type == "skill":
                        power = self._get_skill_power(active_skill)
                        cost = self._get_skill_cost(active_skill)
                        dmg = max(1, power)
                        applied = target.take_damage(dmg, ignore_defense=True)
                        if cost > 0:
                            self.player.take_damage(cost, ignore_defense=True)
                    else:
                        dmg = max(1, (self.player.attack + 1) - target.defense)
                        applied = target.take_damage(dmg)
                    if self.on_player_attack:
                        self.on_player_attack(self.player, target, applied, enemies)
                    if not target.is_alive() and self.on_enemy_defeated:
                        self.on_enemy_defeated(target, enemies, self.player)
                        self.total_kills += 1
                        self.total_exp += max(0, target.exp)
                        self.total_money += max(0, target.money)
                        self.player.exp += max(0, target.exp)
                        self.player.money += max(0, target.money)
                else:
                    if not self.player.is_alive():
                        break
                    dmg = max(1, (actor.attack + 1) - self.player.defense)
                    applied = self.player.take_damage(dmg)
                    if self.on_enemy_attack:
                        self.on_enemy_attack(actor, self.player, applied)
            # loop continues until break condition
        return "victory" if self.player.is_alive() else "defeat"

    @staticmethod
    def _default_player_action(player: Chara, enemies: List[Chara]) -> Optional[int]:
        # Simple AI: target the first alive enemy.
        return 0

    def _active_skill_name(self, skill_field) -> Optional[str]:
        if isinstance(skill_field, list) and skill_field:
            return str(skill_field[0])
        if isinstance(skill_field, str):
            return skill_field
        return None

    def _get_skill_power(self, skill_name: Optional[str]) -> int:
        if not skill_name:
            return 1
        entry = self.skill_defs.get(str(skill_name))
        if not entry:
            return 1
        try:
            return int(entry.get("power", 1))
        except Exception:
            return 1

    def _get_skill_cost(self, skill_name: Optional[str]) -> int:
        if not skill_name:
            return 0
        entry = self.skill_defs.get(str(skill_name))
        if not entry:
            return 0
        try:
            return max(0, int(entry.get("cost", 0)))
        except Exception:
            return 0


__all__ = ["BattleSystem"]
