import pygame
from typing import List, Optional

from .constants import SCREEN_HEIGHT, SCREEN_WIDTH, TEXT_COLOR
from .ui import draw_button


class BattleCommandUI:
    """Bottom command bar with arrow-key selection."""

    def __init__(self, bar_height: int = 120, options: Optional[List[str]] = None) -> None:
        self.bar_height = bar_height
        self.options = options or ["戦う", "進む", "逃げる"]
        self.selected = 0
        self.rect = pygame.Rect(0, SCREEN_HEIGHT - bar_height, SCREEN_WIDTH, bar_height)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_LEFT, pygame.K_a):
            self.selected = (self.selected - 1) % len(self.options)
        if event.key in (pygame.K_RIGHT, pygame.K_d):
            self.selected = (self.selected + 1) % len(self.options)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        bar = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 110))
        surface.blit(bar, self.rect.topleft)

        col_w = self.rect.width // len(self.options)
        for idx, label in enumerate(self.options):
            cx = self.rect.left + col_w * idx + col_w // 2
            cy = self.rect.top + self.rect.height // 2
            prefix = "▶ " if idx == self.selected else "   "
            text = prefix + label
            rendered = font.render(text, True, TEXT_COLOR)
            rect = rendered.get_rect(center=(cx, cy))
            surface.blit(rendered, rect)

    def current_option(self) -> str:
        return self.options[self.selected]

    def set_options(self, options: List[str]) -> None:
        self.options = options
        self.selected = 0 if self.options else 0


def layout_button_row(labels: List[str], screen_width: int, screen_height: int, btn_w: int = 180, btn_h: int = 54, gap: int = 20, margin_bottom: int = 24) -> List[dict]:
    total_w = btn_w * len(labels) + gap * (len(labels) - 1)
    start_x = (screen_width - total_w) // 2
    y = screen_height - btn_h - margin_bottom
    return [
        {"text": text, "rect": pygame.Rect(start_x + (btn_w + gap) * i, y, btn_w, btn_h)}
        for i, text in enumerate(labels)
    ]


def draw_button_row(surface: pygame.Surface, buttons: List[dict], font: pygame.font.Font, mouse_pos, mouse_down) -> int | None:
    """Draw buttons and return clicked index or None."""
    for idx, btn in enumerate(buttons):
        clicked = draw_button(surface, btn["rect"], btn["text"], font, mouse_pos, mouse_down)
        if clicked:
            return idx
    return None


__all__ = ["BattleCommandUI", "layout_button_row", "draw_button_row"]
