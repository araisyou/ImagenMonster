import pygame
from pathlib import Path
from typing import List, Optional

from ..battleview import BattleView, draw_stage_cutin, draw_stage_clear
from ..command import BattleCommandUI
from ..chara import Chara
from ..constants import SCREEN_HEIGHT, SCREEN_WIDTH
from ..corridor import Corridor
from ..ui import draw_text
from ..playercreate import load_player_chara, save_player_state
from ..battlesystem import BattleSystem


class BattleScene:
    def __init__(
        self,
        screen: pygame.Surface,
        clock: pygame.time.Clock,
        font: pygame.font.Font,
        title_font: pygame.font.Font,
    ) -> None:
        self.screen = screen
        self.clock = clock
        self.font = font
        self.title_font = title_font
        # Use default Corridor texture path (assets/texture)
        self.corridor = Corridor()
        self.command_ui = BattleCommandUI(options=["戦う", "にげる"])
        self.chara_view = BattleView()
        self.skill_label = "スキル"
        self._refresh_skill_label()
        self.player_surface: Optional[pygame.Surface] = None
        self._player_surface_evo: Optional[int] = None
        # Stage / enemy fade state
        self.stage_total = 3
        self.stage_index = 1
        self.stage_enemy_counts = [1, 2, 3]
        self.fade_speed = 1.8  # alpha per second
        self.cutin_timer = 0.0
        self.cutin_duration = 1.2
        self.clear_timer = 0.0
        self.clear_duration = 1.5
        self.stage_cleared = False
        self.state = "cutin"  # cutin -> enemy_in -> idle
        self.in_submenu = False
        self.escaped = False
        self.result: str | None = None
        self._feed_items = []
        # current enemies for rendering
        self.current_enemies: list[Chara] = []
        self.enemy_alpha: dict[int, float] = {}
        # no per-enemy fade in this system-driven flow
        self._time_sec = 0.0
        self._guard_active = False
        self._guard_base_defense: int | None = None

    def run(self) -> None:
        bundle = load_player_chara()
        if bundle:
            _, feed_items = bundle
            self._feed_items = feed_items
        system = BattleSystem(
            max_stage=self.stage_total,
            player_action=self._player_action,
            on_enemy_defeated=self._on_enemy_defeated,
            on_stage_start=self._on_stage_start,
            on_player_attack=self._on_player_attack,
            on_enemy_attack=self._on_enemy_attack,
        )
        outcome = system.run()
        self.result = outcome.get("result") if isinstance(outcome, dict) else None
        if self.result == "escape":
            self._persist_result(system, outcome)
            self._show_result_overlay(outcome)
            return
        if self.result == "victory":
            self._persist_result(system, outcome)
            self._show_result_overlay(outcome)
            return
        # defeat case
        self._persist_result(system, outcome)
        self._show_result_overlay(outcome)

    def _player_action(self, player: Chara, enemies: List[Chara]) -> int | None:
        if self._guard_active and self._guard_base_defense is not None:
            player.defense = self._guard_base_defense
            self._guard_active = False
            self._guard_base_defense = None

        target_idx = 0
        mode = "command"  # command(root) -> attack_menu -> target
        action_type = "attack"
        self.command_ui.set_options(["たたかう", "にげる"])
        waiting = True
        pygame.event.clear(pygame.KEYDOWN)
        while waiting:
            if not enemies:
                return None
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if mode == "command":
                    self.command_ui.handle_event(event)
                    if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        action = self.command_ui.current_option()
                        if action == "にげる":
                            return None  # signal escape
                        if action == "たたかう":
                            self.command_ui.set_options(["こうげき", "ぼうぎょ", self.skill_label])
                            mode = "attack_menu"
                elif mode == "attack_menu":
                    self.command_ui.handle_event(event)
                    if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        action = self.command_ui.current_option()
                        if action == "ぼうぎょ":
                            self._start_guard(player)
                            self.command_ui.set_options(["たたかう", "にげる"])
                            return -2  # sentinel for guard
                        if action == self.skill_label:
                            action_type = "skill"
                            mode = "target"
                        else:
                            action_type = "attack"
                            mode = "target"
                else:
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            target_idx = (target_idx - 1) % len(enemies)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            target_idx = (target_idx + 1) % len(enemies)
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            waiting = False
                            break
                self._draw_player_choice(player, enemies, target_idx, mode, enemy_alphas=self._alphas_for(enemies))
            pygame.display.flip()
            self.clock.tick(60)
        # Reset root command options after an action selection finishes
        self.command_ui.set_options(["たたかう", "にげる"])
        if action_type == "skill":
            return (target_idx, "skill")
        return target_idx

    def _start_guard(self, player: Chara) -> None:
        if not self._guard_active:
            self._guard_base_defense = player.defense
            player.defense = player.defense * 2
            self._guard_active = True

    def _on_enemy_defeated(self, defeated: Chara, enemies: List[Chara], player: Chara) -> None:
        if defeated not in enemies:
            return
        idx = enemies.index(defeated)
        alphas = self._alphas_for(enemies)
        fade_speed = 2.5  # alpha per second
        while alphas[idx] > 0:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
            dt = self.clock.tick(60) / 1000.0
            alphas[idx] = max(0.0, alphas[idx] - fade_speed * dt)
            self._draw_player_choice(player, enemies, idx, mode="target", enemy_alphas=alphas)
            pygame.display.flip()
        self.enemy_alpha[id(defeated)] = 0.0
        pygame.event.clear(pygame.KEYDOWN)
        if self.stage_index == self.stage_total and not self.stage_cleared:
            if all(not e.is_alive() for e in enemies):
                self.stage_cleared = True
                self._play_stage_clear()

    def _on_stage_start(self, enemies: List[Chara], stage: int) -> None:
        self.stage_index = stage
        self.current_enemies = enemies
        self.command_ui.set_options(["たたかう", "にげる"])
        self._play_stage_cutin(stage, advance=stage > 1)
        # Fade-in enemies when a new stage begins
        self.enemy_alpha = {id(e): 0.0 for e in enemies}
        alphas = [0.0 for _ in enemies]
        fade_speed = 2.0  # alpha per second
        target_idx = 0 if enemies else -1
        while any(a < 0.99 for a in alphas):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
            dt = self.clock.tick(60) / 1000.0
            alphas = [min(1.0, a + fade_speed * dt) for a in alphas]
            # Show command UI immediately on stage start
            self._draw_player_choice(self._player_stub(), enemies, target_idx, mode="command", enemy_alphas=alphas)
            pygame.display.flip()
        # store final alphas
        for enemy, a in zip(enemies, alphas):
            self.enemy_alpha[id(enemy)] = a
        pygame.event.clear(pygame.KEYDOWN)

    def _play_stage_cutin(self, stage: int, advance: bool = True) -> None:
        """Advance the corridor (optional) and show the stage cut-in overlay."""
        if advance:
            self.corridor.start_advance()
        timer = 0.0
        duration = max(self.cutin_duration, 1.0)
        while (advance and self.corridor.advancing) or timer < duration:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
            dt = self.clock.tick(60) / 1000.0
            timer += dt
            self._time_sec += dt
            if advance:
                self.corridor.update(dt)
            self.corridor.draw(self.screen, self._time_sec)
            draw_stage_cutin(self.screen, stage, self.stage_total)
            pygame.display.flip()
        pygame.event.clear(pygame.KEYDOWN)

    def _play_stage_clear(self) -> None:
        """Show a stage clear cut-in overlay."""
        timer = 0.0
        duration = max(self.clear_duration, 1.0)
        while timer < duration:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
            dt = self.clock.tick(60) / 1000.0
            timer += dt
            self._time_sec += dt
            self.corridor.draw(self.screen, self._time_sec)
            draw_stage_clear(self.screen)
            pygame.display.flip()
        pygame.event.clear(pygame.KEYDOWN)

    def _on_player_attack(self, attacker: Chara, target: Chara, damage: int, enemies: List[Chara]) -> None:
        # After player attack, refresh command view promptly
        self.command_ui.set_options(["たたかう", "にげる"])
        self._draw_player_choice(attacker, enemies, 0, mode="command", enemy_alphas=self._alphas_for(enemies))
        pygame.display.flip()
        # small delay before enemy turn processing
        self.clock.tick(2)

    def _on_enemy_attack(self, attacker: Chara, player: Chara, damage: int) -> None:
        # Show top message for enemy attack, then brief pause
        self._draw_player_choice(player, self.current_enemies, 0, mode="command", enemy_alphas=self._alphas_for(self.current_enemies))
        overlay = self._draw_top_message(f"{attacker.name} のこうげき! {damage}ダメージ")
        pygame.display.flip()
        # wait ~1s, then fade out the cut-in; block input during fade
        wait_time = 1.0
        elapsed = 0.0
        while elapsed < wait_time:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
            dt = self.clock.tick(60) / 1000.0
            elapsed += dt
        # fade out overlay
        fade = 1.0
        fade_speed = 2.0  # alpha per second
        while fade > 0:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
            dt = self.clock.tick(60) / 1000.0
            fade = max(0.0, fade - fade_speed * dt)
            self._draw_player_choice(player, self.current_enemies, 0, mode="command", enemy_alphas=self._alphas_for(self.current_enemies))
            self._blit_overlay_with_alpha(overlay, fade)
            pygame.display.flip()

    def _persist_result(self, system, outcome: dict) -> None:
        # Save player state (hp/exp/money) after battle
        try:
            player = system.player
            save_player_state(player, self._feed_items)
        except Exception:
            pass

    def _show_result_overlay(self, outcome: dict) -> None:
        # Display simple result summary then return
        result = outcome.get("result", "")
        kills = outcome.get("kills", 0)
        money = outcome.get("money", 0)
        exp = outcome.get("exp", 0)
        hp = outcome.get("hp", 0)
        text_title = "STAGE CLEAR" if result == "victory" else "にげる" if result == "escape" else "RESULT"
        duration = 2.5
        timer = 0.0
        while timer < duration:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
            dt = self.clock.tick(60) / 1000.0
            timer += dt
            self.corridor.draw(self.screen, self._time_sec)
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            draw_text(self.screen, text_title, (self.screen.get_width() // 2 - 80, 120), self.title_font)
            draw_text(self.screen, f"撃破: {kills}", (self.screen.get_width() // 2 - 80, 180), self.font)
            draw_text(self.screen, f"Exp +{exp}", (self.screen.get_width() // 2 - 80, 210), self.font)
            draw_text(self.screen, f"Money +{money}", (self.screen.get_width() // 2 - 80, 240), self.font)
            draw_text(self.screen, f"HP {hp}", (self.screen.get_width() // 2 - 80, 270), self.font)
            pygame.display.flip()

    def _player_stub(self) -> Chara:
        # Minimal stub for display when system invokes stage start before first player action
        bundle = load_player_chara()
        if bundle:
            return bundle[0]
        return Chara(name="Player", hp=10, max_hp=10, attack=3, defense=1, agility=1)

    def _alphas_for(self, enemies: List[Chara]) -> List[float]:
        if not enemies:
            return []
        return [self.enemy_alpha.get(id(e), 1.0) for e in enemies]

    def _draw_top_message(self, text: str) -> pygame.Surface:
        band_h = 80
        rect = pygame.Rect(0, 0, self.screen.get_width(), band_h)
        rect.centery = int(self.screen.get_height() * 0.15)
        band = pygame.Surface(rect.size, pygame.SRCALPHA)
        band.fill((0, 0, 0, 200))
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.blit(band, rect.topleft)
        msg_font = self.title_font
        txt = msg_font.render(text, True, (240, 240, 255))
        overlay.blit(txt, txt.get_rect(center=rect.center))
        self.screen.blit(overlay, (0, 0))
        return overlay

    def _blit_overlay_with_alpha(self, overlay: pygame.Surface, alpha: float) -> None:
        temp = overlay.copy()
        temp.set_alpha(int(alpha * 255))
        self.screen.blit(temp, (0, 0))

    def _draw_player_choice(self, player: Chara, enemies: List[Chara], target_idx: int, mode: str, enemy_alphas: List[float] | None = None) -> None:
        time_sec = 0.0
        self.corridor.update(0)
        self.corridor.draw(self.screen, time_sec)
        self.current_enemies = enemies
        self.chara_view.set_enemy_charas(self.current_enemies)
        evo = getattr(player, "evo", 1) or 1
        if self._player_surface_evo != evo or self.player_surface is None:
            self.player_surface = self._load_player_surface(evo)
            self._player_surface_evo = evo
        self.chara_view.set_player(self.player_surface)
        alphas = enemy_alphas if enemy_alphas is not None else self._alphas_for(enemies)
        self.chara_view.draw(self.screen, enemy_alphas=alphas)
        draw_text(self.screen, "Battle Scene", (24, 20), self.title_font)
        draw_text(self.screen, f"Stage {self.stage_index} / {self.stage_total}", (SCREEN_WIDTH - 220, 20), self.font)
        prompt = "コマンド選択" if mode != "target" else f"ターゲット: {enemies[target_idx].name}"
        draw_text(self.screen, prompt, (24, 56), self.font)
        draw_text(self.screen, f"HP {player.hp}/{player.max_hp}", (24, 86), self.font)
        for idx, enemy in enumerate(enemies):
            draw_text(self.screen, f"{enemy.name} HP {enemy.hp}/{enemy.max_hp}", (24, 120 + idx * 24), self.font)
        if mode != "target":
            self.command_ui.draw(self.screen, self.font)
        else:
            # show current target indicator
            draw_text(self.screen, "← → でターゲット / Enter 決定", (24, SCREEN_HEIGHT - 80), self.font)
            self._draw_target_arrow(enemies, target_idx)

    def _draw_target_arrow(self, enemies: List[Chara], target_idx: int) -> None:
        rects = self.chara_view.enemy_rects(len(enemies))
        if not rects:
            return
        idx = target_idx % len(rects)
        rect = rects[idx]
        arrow_y = rect.top - 24
        arrow_x = rect.centerx
        pygame.draw.polygon(
            self.screen,
            (255, 240, 120),
            [(arrow_x, arrow_y), (arrow_x - 10, arrow_y + 16), (arrow_x + 10, arrow_y + 16)],
        )

    def _refresh_skill_label(self) -> None:
        bundle = load_player_chara()
        label = "スキル"
        if bundle:
            chara, _ = bundle
            if chara.skill:
                label = str(chara.skill[0])
        self.skill_label = label

    def _load_player_surface(self, evo: int) -> Optional[pygame.Surface]:
        base = Path(__file__).resolve().parents[2] / "Player" / "image" / "output"
        filename = {
            1: "larva_back.png",
            2: "adult_back.png",
            3: "final_back.png",
        }.get(int(evo), "larva_back.png")
        path = base / filename
        if path.is_file():
            try:
                return pygame.image.load(str(path)).convert_alpha()
            except pygame.error as exc:
                print(f"Failed to load battle player image {path}: {exc}")
        else:
            print(f"Battle player image not found at {path}")
        return None

