import math
import os
from pathlib import Path
from typing import Dict, Tuple

import pygame

from .constants import SCREEN_HEIGHT, SCREEN_WIDTH

# Rendering parameters (ported from demo_corridor)
FOV = 520
CORRIDOR_W = 520
CORRIDOR_H = 280
ADVANCE_DIST = 900
ADVANCE_DURATION = 0.55
SLICE_COUNT = 28
SLICE_STEP = 180
TEX_FRONT = 10
TEX_BACK = 8
FLOOR_TILE_X = 180.0
FLOOR_TILE_Z = 180.0
CEIL_TILE_X = 220.0
CEIL_TILE_Z = 220.0
WALL_TILE_Y = 160.0
WALL_TILE_Z = 220.0
MIN_THICK_PX_FLOOR = 3
MIN_THICK_PX_CEIL = 3


def _clamp(x: float, a: float, b: float) -> float:
    return a if x < a else b if x > b else x


def _ease_in_out(t: float) -> float:
    t = _clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _project(x: float, y: float, z: float, camera_z: float, cx: float, cy: float) -> Tuple[float, float, float] | None:
    dz = z - camera_z
    if dz <= 1:
        return None
    s = FOV / dz
    sx = cx + x * s
    sy = cy + y * s
    return (sx, sy, s)


def _shade(color: Tuple[int, int, int], k: float) -> Tuple[int, int, int]:
    return (int(color[0] * k), int(color[1] * k), int(color[2] * k))


def _make_checker(size: int = 256, tile: int = 16, c1=(60, 60, 90), c2=(30, 30, 48)) -> pygame.Surface:
    surf = pygame.Surface((size, size)).convert()
    for y in range(0, size, tile):
        for x in range(0, size, tile):
            surf.fill(c1 if ((x // tile + y // tile) % 2 == 0) else c2, (x, y, tile, tile))
    return surf


def _make_bricks(w: int = 256, h: int = 256) -> pygame.Surface:
    surf = pygame.Surface((w, h)).convert()
    surf.fill((35, 35, 55))
    brick_h = 18
    brick_w = 42
    mortar = (20, 20, 30)
    brick1 = (55, 45, 65)
    brick2 = (48, 40, 60)

    for y in range(0, h, brick_h):
        offset = (brick_w // 2) if (y // brick_h) % 2 == 1 else 0
        for x in range(-offset, w, brick_w):
            rect = pygame.Rect(x, y, brick_w - 2, brick_h - 2)
            col = brick1 if ((x // brick_w) % 2 == 0) else brick2
            pygame.draw.rect(surf, col, rect)
            pygame.draw.rect(surf, mortar, rect, 1)
    return surf


def _make_grid(w: int = 256, h: int = 256) -> pygame.Surface:
    surf = pygame.Surface((w, h)).convert()
    surf.fill((20, 20, 34))
    line = (55, 55, 80)
    for x in range(0, w, 16):
        pygame.draw.line(surf, line, (x, 0), (x, h), 1)
    for y in range(0, h, 16):
        pygame.draw.line(surf, line, (0, y), (w, y), 1)
    return surf


def _load_texture(path: Path | None, fallback_func) -> pygame.Surface:
    if path and path.exists():
        try:
            return pygame.image.load(str(path)).convert()
        except Exception:
            pass
    return fallback_func()


def _ensure_min_thickness_quad(pts, min_px=3, direction="up", max_expand_px=6):
    nearL, nearR, farR, farL = pts

    y_far = (farL[1] + farR[1]) * 0.5
    y_near = (nearL[1] + nearR[1]) * 0.5
    dy = y_near - y_far

    if dy <= 0:
        return pts
    if dy >= min_px:
        return pts

    need = min(min_px - dy, max_expand_px)

    if direction == "up":
        farL = (farL[0], farL[1] - need)
        farR = (farR[0], farR[1] - need)
    else:
        farL = (farL[0], farL[1] + need)
        farR = (farR[0], farR[1] + need)

    return [nearL, nearR, farR, farL]


def _draw_textured_quad_scanlines(screen, tex, pts, uvs, cache, y_step=3):
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


def _draw_infinite_corridor(screen: pygame.Surface, camera_z: float, time_sec: float, textures, width: int, height: int, caches: Dict) -> None:
    shake = math.sin(time_sec * 6.0) * 2.0
    cx = width // 2 + int(shake)
    cy = height // 2 - 10

    screen.fill((10, 10, 16))

    start_z = camera_z + 80
    quads = []
    zs = []

    for i in range(SLICE_COUNT):
        z = start_z + i * SLICE_STEP
        pts = [
            _project(-CORRIDOR_W, -CORRIDOR_H, z, camera_z, cx, cy),
            _project(CORRIDOR_W, -CORRIDOR_H, z, camera_z, cx, cy),
            _project(CORRIDOR_W, CORRIDOR_H, z, camera_z, cx, cy),
            _project(-CORRIDOR_W, CORRIDOR_H, z, camera_z, cx, cy),
        ]
        if any(p is None for p in pts):
            continue
        quads.append([(p[0], p[1]) for p in pts])
        zs.append(z)

    if len(quads) < 2:
        return

    fog_overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    fog_overlay.fill((0, 0, 0, 0))

    floor_tex = textures["floor"]
    wall_tex = textures["wall"]
    ceil_tex = textures["ceiling"]

    cache_floor = caches.setdefault("floor", {})
    cache_wall = caches.setdefault("wall", {})
    cache_ceil = caches.setdefault("ceiling", {})

    seg_count = len(quads) - 1

    for i in range(seg_count - 1, -1, -1):
        q1 = quads[i]
        q2 = quads[i + 1]
        z1 = zs[i]
        z2 = zs[i + 1]

        mid_z = (z1 + z2) * 0.5
        dz = mid_z - camera_z
        fog = 1.0 - (dz / (SLICE_COUNT * SLICE_STEP * 1.05))
        fog = _clamp(fog, 0.18, 1.0)

        c_floor = _shade((38, 38, 60), fog)
        c_ceiling = _shade((20, 20, 34), fog)
        c_wall = _shade((26, 26, 48), fog)
        c_line = _shade((80, 80, 120), fog)

        floor_pts = [q1[3], q1[2], q2[2], q2[3]]
        ceil_pts = [q1[0], q1[1], q2[1], q2[0]]
        left_pts = [q1[0], q1[3], q2[3], q2[0]]
        right_pts = [q1[1], q1[2], q2[2], q2[1]]

        floor_pts = _ensure_min_thickness_quad(floor_pts, min_px=MIN_THICK_PX_FLOOR, direction="up")
        ceil_pts = _ensure_min_thickness_quad(ceil_pts, min_px=MIN_THICK_PX_CEIL, direction="down")

        # UV for floor
        tw, th = floor_tex.get_size()
        floor_uv = [
            ((-CORRIDOR_W / FLOOR_TILE_X) * tw, (z1 / FLOOR_TILE_Z) * th),
            ((CORRIDOR_W / FLOOR_TILE_X) * tw, (z1 / FLOOR_TILE_Z) * th),
            ((CORRIDOR_W / FLOOR_TILE_X) * tw, (z2 / FLOOR_TILE_Z) * th),
            ((-CORRIDOR_W / FLOOR_TILE_X) * tw, (z2 / FLOOR_TILE_Z) * th),
        ]

        # UV for ceiling
        twc, thc = ceil_tex.get_size()
        ceil_uv = [
            ((-CORRIDOR_W / CEIL_TILE_X) * twc, (z1 / CEIL_TILE_Z) * thc),
            ((CORRIDOR_W / CEIL_TILE_X) * twc, (z1 / CEIL_TILE_Z) * thc),
            ((CORRIDOR_W / CEIL_TILE_X) * twc, (z2 / CEIL_TILE_Z) * thc),
            ((-CORRIDOR_W / CEIL_TILE_X) * twc, (z2 / CEIL_TILE_Z) * thc),
        ]

        # UV for walls
        tww, thw = wall_tex.get_size()
        left_uv = [
            ((z1 / WALL_TILE_Z) * tww, (-CORRIDOR_H / WALL_TILE_Y) * thw),
            ((z1 / WALL_TILE_Z) * tww, (CORRIDOR_H / WALL_TILE_Y) * thw),
            ((z2 / WALL_TILE_Z) * tww, (CORRIDOR_H / WALL_TILE_Y) * thw),
            ((z2 / WALL_TILE_Z) * tww, (-CORRIDOR_H / WALL_TILE_Y) * thw),
        ]
        right_uv = [
            (-(z1 / WALL_TILE_Z) * tww, (-CORRIDOR_H / WALL_TILE_Y) * thw),
            (-(z1 / WALL_TILE_Z) * tww, (CORRIDOR_H / WALL_TILE_Y) * thw),
            (-(z2 / WALL_TILE_Z) * tww, (CORRIDOR_H / WALL_TILE_Y) * thw),
            (-(z2 / WALL_TILE_Z) * tww, (-CORRIDOR_H / WALL_TILE_Y) * thw),
        ]

        _draw_textured_quad_scanlines(screen, floor_tex, floor_pts, floor_uv, cache_floor, y_step=1)
        _draw_textured_quad_scanlines(screen, ceil_tex, ceil_pts, ceil_uv, cache_ceil, y_step=1)
        _draw_textured_quad_scanlines(screen, wall_tex, left_pts, left_uv, cache_wall, y_step=3)
        _draw_textured_quad_scanlines(screen, wall_tex, right_pts, right_uv, cache_wall, y_step=3)

        fog_alpha = int((1.0 - fog) * 175)
        if fog_alpha > 0:
            pygame.draw.polygon(fog_overlay, (0, 0, 0, fog_alpha), floor_pts)
            pygame.draw.polygon(fog_overlay, (0, 0, 0, fog_alpha), ceil_pts)
            pygame.draw.polygon(fog_overlay, (0, 0, 0, fog_alpha), left_pts)
            pygame.draw.polygon(fog_overlay, (0, 0, 0, fog_alpha), right_pts)

        if i % 2 == 0:
            pygame.draw.line(screen, c_line, q2[3], q2[2], 2)

    screen.blit(fog_overlay, (0, 0))


class Corridor:
    """Reusable corridor renderer with advance animation trigger."""

    def __init__(self, texture_dir: str | os.PathLike | None = None, width: int = SCREEN_WIDTH, height: int = SCREEN_HEIGHT) -> None:
        self.width = width
        self.height = height
        base_dir = Path(texture_dir) if texture_dir else Path(__file__).resolve().parent.parent / "assets" / "texture"
        self.textures = {
            "floor": _load_texture(base_dir / "floor.png", lambda: _make_checker(256, 16)),
            "wall": _load_texture(base_dir / "wall.png", lambda: _make_bricks(256, 256)),
            "ceiling": _load_texture(base_dir / "ceiling.png", lambda: _make_grid(256, 256)),
        }

        self.camera_z = 0.0
        self.advancing = False
        self.advance_t = 0.0
        self._advance_start_z = 0.0
        self._caches: Dict[str, Dict] = {}

    def start_advance(self) -> None:
        if self.advancing:
            return
        self.advancing = True
        self.advance_t = 0.0
        self._advance_start_z = self.camera_z

    def update(self, dt: float) -> None:
        if not self.advancing:
            return
        self.advance_t += dt / ADVANCE_DURATION
        t01 = _clamp(self.advance_t, 0.0, 1.0)
        self.camera_z = self._advance_start_z + ADVANCE_DIST * _ease_in_out(t01)
        if t01 >= 1.0:
            self.advancing = False

    def draw(self, surface: pygame.Surface, time_sec: float) -> None:
        _draw_infinite_corridor(surface, self.camera_z, time_sec, self.textures, self.width, self.height, self._caches)


__all__ = ["Corridor"]
