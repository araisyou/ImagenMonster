import pygame
from typing import Optional, Sequence, Mapping

from .grass import Grass
from .ui import draw_text
from .feedview import draw_feed_mode
from .shopview import draw_shop
from .constants import SCREEN_HEIGHT, SCREEN_WIDTH


class HomeView:
    """Simple home screen view that draws the ground plane."""

    def __init__(self, width: int = SCREEN_WIDTH, height: int = SCREEN_HEIGHT) -> None:
        self.width = width
        self.height = height
        self.grass = Grass(width=width, height=height)
        self.player_color = (90, 180, 255)
        self.player_size = 200

    def draw_player(self, surface: pygame.Surface, sprite: Optional[pygame.Surface] = None, alpha: float = 1.0) -> None:
        size = self.player_size
        rect = pygame.Rect(0, 0, size, size)
        rect.center = (self.width // 2, int(self.height * 0.57))
        if sprite:
            scaled = pygame.transform.smoothscale(sprite, rect.size).convert_alpha()
            scaled.set_alpha(int(255 * alpha))
            surface.blit(scaled, rect)
        else:
            square = pygame.Surface(rect.size, pygame.SRCALPHA)
            square.fill(self.player_color + (int(255 * alpha),))
            pygame.draw.rect(square, (20, 40, 60, int(255 * alpha)), square.get_rect(), 3, border_radius=8)
            surface.blit(square, rect)

    def draw(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        title_font: pygame.font.Font,
        time_sec: float,
        command_bar,
        feed_mode: bool,
        shop_mode: bool,
        feed_items: Sequence,
        status: Mapping[str, object],
        level: int,
        skill: str,
        feed_selecting: bool,
        feed_selected_index: int,
        skill_info: Mapping[str, object] | None = None,
        player_surface: Optional[pygame.Surface] = None,
        shop_items=None,
        shop_selected: int = 0,
        money: int = 0,
        info: Optional[str] = None,
        center_message: Optional[str] = None,
    ) -> None:
        self.grass.draw(surface, time_sec)
        draw_text(surface, "Home", (24, 20), title_font)
        self.draw_player(surface, player_surface)
        if feed_mode:
            draw_feed_mode(
                surface,
                font,
                title_font,
                feed_items,
                status,
                level,
                skill,
                skill_info=skill_info,
                selecting=feed_selecting,
                selected_index=feed_selected_index,
            )
        if shop_mode:
            draw_shop(
                surface,
                font,
                title_font,
                shop_items or [],
                selecting=True,
                selected_index=shop_selected,
                money=money,
            )
        command_bar.draw(surface, font)
        if info:
            draw_text(surface, info, (24, 60), font)
        if center_message:
            self._draw_center_message(surface, center_message, title_font)

    def _draw_center_message(self, surface: pygame.Surface, text: str, title_font: pygame.font.Font) -> None:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        rect = pygame.Rect(0, 0, surface.get_width(), 140)
        rect.centery = int(surface.get_height() * 0.2)
        band = pygame.Surface(rect.size, pygame.SRCALPHA)
        band.fill((0, 0, 0, 220))
        surface.blit(band, rect.topleft)

        txt = title_font.render(text, True, (240, 240, 255))
        surface.blit(txt, txt.get_rect(center=rect.center))


__all__ = ["HomeView"]
