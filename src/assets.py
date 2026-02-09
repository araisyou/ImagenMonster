import os
import pygame

from .constants import PANEL_COLOR


def load_image(path: str, max_size: tuple[int, int]) -> pygame.Surface:
    """画像を読み込み、最大サイズ内に収まるようアスペクト比を維持して縮小する。"""
    if os.path.exists(path):
        image = pygame.image.load(path).convert_alpha()
        img_w, img_h = image.get_size()
        max_w, max_h = max_size
        scale = min(max_w / img_w, max_h / img_h, 1.0)  # 拡大はしない
        if scale < 1.0:
            new_size = (int(img_w * scale), int(img_h * scale))
            image = pygame.transform.smoothscale(image, new_size)
        return image

    placeholder = pygame.Surface(max_size)
    placeholder.fill(PANEL_COLOR)
    pygame.draw.rect(placeholder, (120, 120, 140), placeholder.get_rect(), 4)
    pygame.draw.line(placeholder, (120, 120, 140), (0, 0), (max_size[0], max_size[1]), 3)
    pygame.draw.line(placeholder, (120, 120, 140), (0, max_size[1]), (max_size[0], 0), 3)
    return placeholder
