import pygame
from typing import Mapping, Sequence

from .battlesystem import _load_skill_defs

from .ui import draw_text
from .item import Item


def draw_feed_mode(
    surface: pygame.Surface,
    font: pygame.font.Font,
    title_font: pygame.font.Font,
    feed_items: Sequence[Item],
    status: Mapping[str, object],
    level: int,
    skill: str,
    skill_info: Mapping[str, object] | None = None,
    selecting: bool = False,
    selected_index: int = 0,
) -> None:
    w, h = surface.get_size()
    left = pygame.Rect(40, 140, w // 2 - 180, h - 240)
    right = pygame.Rect(w // 2 + 140, 140, w // 2 - 180, h - 240)

    def draw_translucent(rect: pygame.Rect) -> None:
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((90, 90, 90, 140))
        pygame.draw.rect(panel, (30, 30, 30, 180), panel.get_rect(), 2, border_radius=10)
        surface.blit(panel, rect.topleft)

    draw_translucent(left)
    draw_translucent(right)

    draw_text(surface, "えさ一覧", (left.x + 12, left.y + 8), title_font)
    y = left.y + 56
    for idx, item in enumerate(feed_items):
        prefix = "▶ " if selecting and idx == selected_index else "  "
        draw_text(surface, f"{prefix}{item.name} ({item.heal})", (left.x + 16, y), font)
        y += 28

    draw_text(surface, "ステータス", (right.x + 12, right.y + 8), title_font)
    y = right.y + 56
    draw_text(surface, f"レベル: {level}", (right.x + 16, y), font)
    y += 28
    order = ["HP", "攻撃", "防御", "俊敏"]
    for k in order:
        if k in status:
            draw_text(surface, f"{k}: {status[k]}", (right.x + 16, y), font)
            y += 28
        if k == "俊敏":
            draw_text(surface, f"必殺技: {skill}", (right.x + 16, y), font)
            y += 28
            info = skill_info or _lookup_skill(skill)
            power = info.get("power") if info else None
            cost = info.get("cost") if info else None
            draw_text(surface, f"  パワー: {power if power is not None else '-'}", (right.x + 32, y), font)
            y += 24
            draw_text(surface, f"  コスト: {cost if cost is not None else '-'}", (right.x + 32, y), font)
            y += 24


def _lookup_skill(name: str | None) -> Mapping[str, object] | None:
    if not name:
        return None
    try:
        defs = _load_skill_defs()
        return defs.get(str(name))
    except Exception:
        return None


__all__ = ["draw_feed_mode"]
