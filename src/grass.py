import math
import os
from pathlib import Path
from typing import Dict, Tuple

import pygame

from .constants import SCREEN_HEIGHT, SCREEN_WIDTH

# Simple ground-only renderer inspired by corridor.py (floor part only)
FOV = 520
GROUND_W = 3000
GROUND_H = 600
SLICE_COUNT = 28
SLICE_STEP = 120
FLOOR_TILE_X = 180.0
FLOOR_TILE_Z = 180.0
MIN_THICK_PX_FLOOR = 3


def _clamp(x: float, a: float, b: float) -> float:
    return a if x < a else b if x > b else x


def _project(x: float, y: float, z: float, camera_z: float, cx: float, cy: float) -> Tuple[float, float, float] | None:
    dz = z - camera_z
    if dz <= 1:
        return None
    s = FOV / dz
    sx = cx + x * s
    sy = cy + y * s
    return (sx, sy, s)


def _make_checker(size: int = 256, tile: int = 16, c1=(70, 120, 70), c2=(40, 80, 40)) -> pygame.Surface:
    surf = pygame.Surface((size, size)).convert()
    for y in range(0, size, tile):
        for x in range(0, size, tile):
            surf.fill(c1 if ((x // tile + y // tile) % 2 == 0) else c2, (x, y, tile, tile))
    return surf


def _load_texture(path: Path | None, fallback_func) -> pygame.Surface:
    if path and path.exists():
        try:
            return pygame.image.load(str(path)).convert()
        except Exception:
            pass
    return fallback_func()


def _ensure_min_thickness_quad(pts, min_px=3, max_expand_px=6):
    nearL, nearR, farR, farL = pts
    y_far = (farL[1] + farR[1]) * 0.5
    y_near = (nearL[1] + nearR[1]) * 0.5
    dy = y_near - y_far
    if dy <= 0:
        return pts
    if dy >= min_px:
        return pts
    need = min(min_px - dy, max_expand_px)
    farL = (farL[0], farL[1] - need)
    farR = (farR[0], farR[1] - need)
    return [nearL, nearR, farR, farL]


def _draw_textured_quad_scanlines(screen, tex, pts, uvs, cache: Dict, y_step=2):
    tw, th = tex.get_size()
    min_y = int(max(0, min(p[1] for p in pts)))
    max_y = int(min(screen.get_height() - 1, max(p[1] for p in pts)))
    if max_y <= min_y:
        return

    def edge_intersect(p1, p2, uv1, uv2, y):
        x1, y1 = p1
        x2, y2 = p2
        if y1 == y2:
            return None
        if (y < min(y1, y2)) or (y >= max(y1, y2)):
            return None
        t = (y - y1) / (y2 - y1)
        x = x1 + (x2 - x1) * t
        u = uv1[0] + (uv2[0] - uv1[0]) * t
        v = uv1[1] + (uv2[1] - uv1[1]) * t
        return (x, u, v)

    def get_row2(vv):
        key = (id(tex), vv)
        cached = cache.get(key)
        if cached is not None:
            return cached
        row = tex.subsurface((0, vv, tw, 1))
        r2 = pygame.Surface((tw * 2, 1)).convert()
        r2.blit(row, (0, 0))
        r2.blit(row, (tw, 0))
        cache[key] = r2
        return r2

    for y in range(min_y, max_y + 1, y_step):
        inter = []
        for i in range(4):
            p1 = pts[i]
            p2 = pts[(i + 1) % 4]
            uv1 = uvs[i]
            uv2 = uvs[(i + 1) % 4]
            hit = edge_intersect(p1, p2, uv1, uv2, y)
            if hit is not None:
                inter.append(hit)
        if len(inter) < 2:
            continue
        inter.sort(key=lambda t: t[0])
        xL, uL, vL = inter[0]
        xR, uR, vR = inter[-1]
        if xR <= xL + 1:
            continue
        w = int(xR - xL)
        if w <= 1:
            continue
        vv = int((vL + vR) * 0.5) % th
        u_mid = (uL + uR) * 0.5
        off = int(u_mid) % tw
        row2 = get_row2(vv)
        seg = row2.subsurface((off, 0, tw, 1))
        strip_h = y_step
        if y + strip_h > max_y + 1:
            strip_h = max(1, (max_y + 1) - y)
        scaled = pygame.transform.scale(seg, (w, strip_h))
        screen.blit(scaled, (int(xL), y))


class Grass:
    """Ground-only pseudo-3D plane (floor slice from corridor)."""

    def __init__(self, texture_dir: str | os.PathLike | None = None, width: int = SCREEN_WIDTH, height: int = SCREEN_HEIGHT) -> None:
        self.width = width
        self.height = height
        base_dir = Path(texture_dir) if texture_dir else Path(__file__).resolve().parent.parent / "assets" / "texture"
        self.floor_tex = _load_texture(base_dir / "grass.png", lambda: _make_checker())
        self.cache_floor: Dict = {}
        self.camera_z = 0.0

    def draw(self, surface: pygame.Surface, time_sec: float = 0.0) -> None:
        cx = self.width // 2
        cy = self.height // 2 - 10

        surface.fill((10, 10, 16))

        start_z = self.camera_z + 80
        quads = []
        zs = []
        for i in range(SLICE_COUNT):
            z = start_z + i * SLICE_STEP
            pts = [
                _project(-GROUND_W, -GROUND_H, z, self.camera_z, cx, cy),
                _project(GROUND_W, -GROUND_H, z, self.camera_z, cx, cy),
                _project(GROUND_W, GROUND_H, z, self.camera_z, cx, cy),
                _project(-GROUND_W, GROUND_H, z, self.camera_z, cx, cy),
            ]
            if any(p is None for p in pts):
                continue
            quads.append([(p[0], p[1]) for p in pts])
            zs.append(z)
        if len(quads) < 2:
            return

        seg_count = len(quads) - 1
        for i in range(seg_count - 1, -1, -1):
            q1 = quads[i]
            q2 = quads[i + 1]
            z1 = zs[i]
            z2 = zs[i + 1]

            floor_pts = [q1[3], q1[2], q2[2], q2[3]]
            floor_pts = _ensure_min_thickness_quad(floor_pts, min_px=MIN_THICK_PX_FLOOR)

            tw, th = self.floor_tex.get_size()
            floor_uv = [
                ((-GROUND_W / FLOOR_TILE_X) * tw, (z1 / FLOOR_TILE_Z) * th),
                ((GROUND_W / FLOOR_TILE_X) * tw, (z1 / FLOOR_TILE_Z) * th),
                ((GROUND_W / FLOOR_TILE_X) * tw, (z2 / FLOOR_TILE_Z) * th),
                ((-GROUND_W / FLOOR_TILE_X) * tw, (z2 / FLOOR_TILE_Z) * th),
            ]

            _draw_textured_quad_scanlines(surface, self.floor_tex, floor_pts, floor_uv, self.cache_floor, y_step=1)


__all__ = ["Grass"]
