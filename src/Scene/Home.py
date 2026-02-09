import json
import pygame
from pathlib import Path
from typing import Callable, Optional

from ..constants import FPS, SCREEN_WIDTH, SCREEN_HEIGHT
from ..homeview import HomeView
from ..battlesystem import _load_skill_defs
from ..command import BattleCommandUI
from ..ui import draw_text
from ..playercreate import load_player_chara, save_default_player, load_player, save_player_state
from ..item import load_items
from ..chara import Chara

MAX_FEED_ITEMS = 6


class HomeScene:
    def __init__(
        self,
        screen: pygame.Surface,
        clock: pygame.time.Clock,
        font: pygame.font.Font,
        title_font: pygame.font.Font,
        on_battle: Optional[Callable[[], None]] = None,
    ) -> None:
        self.screen = screen
        self.clock = clock
        self.font = font
        self.title_font = title_font
        self.on_battle = on_battle
        self.view = HomeView()
        self.feed_mode = False
        self.shop_mode = False
        self.feed_selected = 0
        self.message_text: Optional[str] = None
        self.message_timer: float = 0.0
        bundle = load_player_chara()
        if bundle is None:
            save_default_player()
            bundle = load_player_chara()
        if bundle is None:
            pdata = load_player() or {}
            self.feed_items = []
            hp = int(pdata.get("hp", 10))
            max_hp = int(pdata.get("max_hp", hp))
            atk = int(pdata.get("attack", 3))
            deff = int(pdata.get("defense", 1))
            agi = int(pdata.get("agility", 1))
            exp = int(pdata.get("exp", 0))
            money = int(pdata.get("money", 0))
            skill = pdata.get("skill") or None
            self.chara = Chara(name="Player", hp=hp, max_hp=max_hp, attack=atk, defense=deff, agility=agi, exp=exp, money=money, skill=skill)
            self.level = self._compute_level(exp)
            self.money = self.chara.money
        else:
            chara, feed_items = bundle
            self.feed_items = feed_items or []
            self.chara = chara
            self.level = self._compute_level(chara.exp)
            self.money = chara.money
        self.chara.evo = self._compute_evo(self.level)
        self._sync_status()
        self.skill_name = self.chara.skill[0] if self.chara.skill else "スキルなし"
        self.skill_defs = _load_skill_defs()
        self.player_surface = self._load_player_surface()
        self.shop_items = load_items()
        self.shop_selected = 0
        self.command_bar = BattleCommandUI(options=["えさやり", "ダンジョン", "ショップ"])

    def run(self) -> None:
        running = True
        time_sec = 0.0
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            time_sec += dt
            if self.message_timer > 0:
                self.message_timer -= dt
                if self.message_timer <= 0:
                    self.message_text = None
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif self.feed_mode and event.key in (pygame.K_UP, pygame.K_w):
                        total = max(1, len(self.feed_items))
                        self.feed_selected = (self.feed_selected - 1) % total
                    elif self.feed_mode and event.key in (pygame.K_DOWN, pygame.K_s):
                        total = max(1, len(self.feed_items))
                        self.feed_selected = (self.feed_selected + 1) % total
                    elif self.shop_mode and event.key in (pygame.K_UP, pygame.K_w):
                        self.shop_selected = (self.shop_selected - 1) % max(1, len(self.shop_items))
                    elif self.shop_mode and event.key in (pygame.K_DOWN, pygame.K_s):
                        self.shop_selected = (self.shop_selected + 1) % max(1, len(self.shop_items))
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        if self.feed_mode:
                            self._trigger_option()
                        elif self.shop_mode:
                            self._confirm_shop()
                        else:
                            self._trigger_option()
                self.command_bar.handle_event(event)

            self.view.draw(
                self.screen,
                self.font,
                self.title_font,
                time_sec,
                command_bar=self.command_bar,
                feed_mode=self.feed_mode,
                shop_mode=self.shop_mode,
                feed_items=self.feed_items,
                status=self.status,
                level=self.level,
                skill=self.skill_name,
                feed_selecting=self.feed_mode,
                feed_selected_index=self.feed_selected,
                skill_info=self._skill_info(self.skill_name),
                player_surface=self.player_surface,
                shop_items=self.shop_items,
                shop_selected=self.shop_selected,
                money=self.money,
                info="Enter/Space: 決定 / Esc: 戻る",
                center_message=self.message_text,
            )
            draw_text(self.screen, "Home Scene", (24, 96), self.font)

            pygame.display.flip()

    def _trigger_option(self) -> None:
        opt = self.command_bar.current_option()
        if self.feed_mode:
            if opt == "あげる":
                self._give_selected_item()
            elif opt == "戻る":
                self.feed_mode = False
                self.command_bar.set_options(["えさやり", "ダンジョン", "ショップ"])
        elif self.shop_mode:
            # ここで購入処理などを追加予定（現状はEnterで_confirm_shopが呼ばれる）
            pass
        else:
            if opt == "えさやり":
                self.feed_mode = True
                self.command_bar.set_options(["あげる", "戻る"])
            elif opt == "ダンジョン":
                if self.on_battle:
                    self.on_battle()
            elif opt == "ショップ":
                self.shop_mode = True
                self.feed_mode = False
                self.command_bar.set_options(["購入", "戻る"])

    def _give_selected_item(self) -> None:
        if not self.feed_items:
            print("えさなし")
            return
        idx = self.feed_selected % len(self.feed_items)
        item = self.feed_items[idx]
        if self.chara.hp >= self.chara.max_hp:
            self._flash_message("これ以上回復しません")
            print("HPは最大です")
            return
        print(f"{item.name} をあげた (+{item.heal})")
        healed = self.chara.heal(item.heal)
        self._sync_status()
        # リストから削除し、選択位置を補正
        self.feed_items.pop(idx)
        if self.feed_items:
            self.feed_selected %= len(self.feed_items)
        else:
            self.feed_selected = 0
        self._persist_player()
        self._flash_message("えさをあげました")

    def _confirm_shop(self) -> None:
        if not self.shop_items:
            print("商品なし")
            return
        opt = self.command_bar.current_option()
        if opt == "購入":
            item = self.shop_items[self.shop_selected % len(self.shop_items)]
            if len(self.feed_items) >= MAX_FEED_ITEMS:
                print("これ以上購入できません (上限6個)")
                self._flash_message("これ以上購入できません")
                return
            if self.money >= item.price:
                self.money -= item.price
                self.feed_items.append(item)
                print(f"{item.name} を購入")
                self._persist_player()
                self._flash_message("購入しました")
            else:
                print("お金が足りません")
                self._flash_message("お金が足りません")
        elif opt == "戻る":
            self.shop_mode = False
            self.command_bar.set_options(["えさやり", "ダンジョン", "ショップ"])

    def _persist_player(self) -> None:
        if hasattr(self, "chara") and self.chara:
            self.chara.money = self.money
            self.chara.evo = self._compute_evo(self.level)
            save_player_state(self.chara, self.feed_items)

    def _skill_info(self, name: str | None) -> dict | None:
        if not name:
            return None
        return self.skill_defs.get(str(name)) if hasattr(self, "skill_defs") else None

    def _flash_message(self, text: str, duration: float = 1.5) -> None:
        self.message_text = text
        self.message_timer = duration

    def _compute_evo(self, level: int) -> int:
        if level >= 20:
            return 3
        if level >= 10:
            return 2
        return 1

    def _load_player_surface(self) -> Optional[pygame.Surface]:
        base = Path(__file__).resolve().parents[2] / "Player" / "image" / "output"
        evo = getattr(self.chara, "evo", 1) or 1
        filename = {
            1: "larva_front.png",
            2: "adult_front.png",
            3: "final_front.png",
        }.get(int(evo), "larva_front.png")
        path = base / filename
        if path.is_file():
            try:
                return pygame.image.load(str(path)).convert_alpha()
            except pygame.error as exc:
                print(f"Failed to load player image {path}: {exc}")
        else:
            print(f"Player image not found at {path}")
        return None

    def _sync_status(self) -> None:
        if hasattr(self, "chara") and self.chara:
            self.status = {
                "HP": f"{self.chara.hp} / {self.chara.max_hp}",
                "攻撃": self.chara.attack,
                "防御": self.chara.defense,
                "俊敏": self.chara.agility,
            }

    def _compute_level(self, exp: int) -> int:
        table_path = Path(__file__).resolve().parents[2] / "Player" / "exp_table.json"
        if table_path.is_file():
            try:
                with table_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    levels = data.get("levels", [])
                    lvl = 1
                    for i, req in enumerate(levels):
                        if exp >= req:
                            lvl = i + 1
                        else:
                            break
                    return lvl
            except json.JSONDecodeError:
                pass
        # fallback: simple thresholds
        thresholds = [0, 10, 30, 60, 100]
        lvl = 1
        for i, req in enumerate(thresholds):
            if exp >= req:
                lvl = i + 1
            else:
                break
        return lvl


__all__ = ["HomeScene"]
