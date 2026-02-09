import pygame
from typing import List, Optional

from .ui import draw_text
from .item import Item


def draw_shop(
    surface: pygame.Surface,
    font: pygame.font.Font,
    title_font: pygame.font.Font,
    items: List[Item],
    selecting: bool = True,
    selected_index: int = 0,
    money: int = 0,
) -> None:
    w, h = surface.get_size()
    left = pygame.Rect(40, 120, w // 2 - 80, h - 220)
    right = pygame.Rect(w // 2 + 40, 120, w // 2 - 80, h - 220)

    def draw_panel(rect: pygame.Rect) -> None:
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((90, 90, 90, 140))
        pygame.draw.rect(panel, (30, 30, 30, 180), panel.get_rect(), 2, border_radius=10)
        surface.blit(panel, rect.topleft)

    draw_panel(left)
    draw_panel(right)

    draw_text(surface, f"ショップ             {money}G", (left.x + 12, left.y + 8), title_font)
    y = left.y + 56
    for idx, item in enumerate(items):
        prefix = "▶ " if selecting and idx == selected_index else "  "
        draw_text(surface, f"{prefix}{item.name} ({item.price}G)", (left.x + 16, y), font)
        y += 28
    if not items:
        draw_text(surface, "商品がありません", (left.x + 16, y), font)

    draw_text(surface, "詳細", (right.x + 12, right.y + 8), title_font)
    y = right.y + 56
    if items:
        sel = items[selected_index % len(items)]
        draw_text(surface, f"名前: {sel.name}", (right.x + 16, y), font); y += 28
        draw_text(surface, f"価格: {sel.price}G", (right.x + 16, y), font); y += 28
        draw_text(surface, f"回復: {sel.heal}", (right.x + 16, y), font); y += 28
        img_path = str(sel.image_path) if sel.image_path else "(なし)"
        draw_text(surface, f"画像: {img_path}", (right.x + 16, y), font); y += 28
    else:
        draw_text(surface, "表示する商品がありません", (right.x + 16, y), font)


__all__ = ["draw_shop"]
