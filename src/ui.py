import pygame

from .constants import BG_COLOR, BUTTON_COLOR, BUTTON_HOVER_COLOR, PANEL_COLOR, TEXT_COLOR


def fill_background(surface: pygame.Surface) -> None:
    surface.fill(BG_COLOR)
    pygame.draw.rect(surface, (26, 26, 34), surface.get_rect(), 12)


def draw_panel(surface: pygame.Surface, rect: pygame.Rect) -> None:
    pygame.draw.rect(surface, PANEL_COLOR, rect, border_radius=8)
    pygame.draw.rect(surface, (14, 14, 18), rect, 2, border_radius=8)


def draw_text(surface: pygame.Surface, text: str, pos: tuple[int, int], font: pygame.font.Font, color=TEXT_COLOR) -> pygame.Rect:
    rendered = font.render(text, True, color)
    surface.blit(rendered, pos)
    return rendered.get_rect(topleft=pos)


def draw_button(
    surface: pygame.Surface,
    rect: pygame.Rect,
    text: str,
    font: pygame.font.Font,
    mouse_pos: tuple[int, int],
    mouse_down: bool,
) -> bool:
    hovered = rect.collidepoint(mouse_pos)
    color = BUTTON_HOVER_COLOR if hovered else BUTTON_COLOR
    pygame.draw.rect(surface, color, rect, border_radius=6)
    pygame.draw.rect(surface, (10, 10, 14), rect, 2, border_radius=6)
    text_surface = font.render(text, True, TEXT_COLOR)
    text_rect = text_surface.get_rect(center=rect.center)
    surface.blit(text_surface, text_rect)
    return hovered and mouse_down
