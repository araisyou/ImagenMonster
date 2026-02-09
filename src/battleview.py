import pygame
from typing import List, Optional

from .constants import SCREEN_HEIGHT, SCREEN_WIDTH
from .chara import Chara

ALLY_COLOR = (96, 160, 240)
ENEMY_COLOR = (200, 90, 90)


class BattleView:
    """Simple character placeholders for battle: player front, up to 3 enemies in the back."""

    def __init__(self, width: int = SCREEN_WIDTH, height: int = SCREEN_HEIGHT) -> None:
        self.width = width
        self.height = height
        self.player_surface: Optional[pygame.Surface] = None
        self.enemy_surfaces: List[Optional[pygame.Surface]] = [None, None, None]

    def set_player(self, surface: Optional[pygame.Surface]) -> None:
        self.player_surface = surface

    def set_enemy_charas(self, charas: List[Chara]) -> None:
        for i in range(3):
            self.enemy_surfaces[i] = None
        for i in range(min(3, len(charas))):
            ch = charas[i]
            surf = ch.surface
            if surf is None and ch.image_path:
                try:
                    img = pygame.image.load(str(ch.image_path)).convert_alpha()
                    ch.surface = img
                    surf = img
                except pygame.error:
                    surf = None
            self.enemy_surfaces[i] = surf

    def draw(self, surface: pygame.Surface, enemy_alphas: Optional[list[float]] = None) -> None:
        # 可視な敵のインデックスを判定（alpha>0で描画対象）
        alive_indices = []
        if enemy_alphas:
            alive_indices = [i for i, a in enumerate(enemy_alphas) if a is not None and a > 0.01]
        else:
            alive_indices = [i for i, s in enumerate(self.enemy_surfaces) if s is not None]

        count = max(1, min(3, len(alive_indices)))
        rects = self.enemy_rects(count)

        # 配置オフセットは可視な敵の順に適用
        for pos_idx, enemy_idx in enumerate(alive_indices[: len(rects)]):
            rect = rects[pos_idx]
            alpha = enemy_alphas[enemy_idx] if enemy_alphas and enemy_idx < len(enemy_alphas) else 1.0
            self._draw_entity(surface, rect, self.enemy_surfaces[enemy_idx], ENEMY_COLOR, alpha)

        # Player (front, overlaps UI a bit)
        player_rect = pygame.Rect(0, 0, 180, 180)
        player_rect.midbottom = (self.width // 2, self.height)
        self._draw_entity(surface, player_rect, self.player_surface, ALLY_COLOR)

    def enemy_rects(self, count: int) -> List[pygame.Rect]:
        count = max(1, min(3, count))
        layouts = {
            1: (self.height // 2 + 60, [0]),
            2: (self.height // 2 + 60, [-90, 90]),
            3: (self.height // 2 + 60, [-100, 0, 100]),
        }
        back_y, x_offsets = layouts[count]
        size = (80, 120)
        rects: List[pygame.Rect] = []
        for x_off in x_offsets:
            rect = pygame.Rect(0, 0, *size)
            rect.midbottom = (self.width // 2 + x_off, back_y)
            rects.append(rect)
        return rects

    def _draw_entity(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        sprite: Optional[pygame.Surface],
        body_color: tuple[int, int, int],
        alpha: float = 1.0,
    ) -> None:
        if sprite:
            scaled = pygame.transform.smoothscale(sprite, rect.size).convert_alpha()
            scaled.set_alpha(int(alpha * 255))
            surface.blit(scaled, rect)
        else:
            body = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(body, body_color + (int(255 * alpha),), body.get_rect(), border_radius=12)
            pygame.draw.rect(body, (0, 0, 0, int(255 * alpha)), body.get_rect(), 2, border_radius=12)
            surface.blit(body, rect)


def draw_stage_cutin(surface: pygame.Surface, x: int, y: int) -> None:
    """Draw a simple stage cut-in overlay with only stage index (x) and total (y).

    Fontsやフェード時間は内部固定。呼び出し側は必要なら呼ぶ回数を制御して演出する。
    """
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    band_h = 120
    rect = pygame.Rect(0, 0, surface.get_width(), band_h)
    rect.centery = surface.get_height() // 2
    band = pygame.Surface(rect.size, pygame.SRCALPHA)
    band.fill((0, 0, 0, 200))
    surface.blit(band, rect.topleft)

    title_font = pygame.font.SysFont(None, 64)
    text = f"STAGE {x} / {y}"
    txt = title_font.render(text, True, (240, 240, 255))
    surface.blit(txt, txt.get_rect(center=rect.center))

def draw_stage_clear(surface: pygame.Surface) -> None:
    """Draw a simple stage clear overlay."""
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surface.blit(overlay, (0, 0))

    rect = pygame.Rect(0, 0, surface.get_width(), 140)
    rect.centery = surface.get_height() // 2
    band = pygame.Surface(rect.size, pygame.SRCALPHA)
    band.fill((0, 0, 0, 220))
    surface.blit(band, rect.topleft)

    title_font = pygame.font.SysFont(None, 64)
    text = "STAGE CLEAR"
    txt = title_font.render(text, True, (240, 240, 255))
    surface.blit(txt, txt.get_rect(center=rect.center))


__all__ = ["BattleView", "draw_stage_cutin", "draw_stage_clear"]
