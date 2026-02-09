import pygame
from pathlib import Path

from ..constants import SCREEN_WIDTH, SCREEN_HEIGHT
from ..ui import draw_text
from ..playercreate import player_path


class GameOverScene:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock, font: pygame.font.Font, title_font: pygame.font.Font) -> None:
        self.screen = screen
        self.clock = clock
        self.font = font
        self.title_font = title_font

    def run(self) -> None:
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    waiting = False
            self._draw()
            pygame.display.flip()
            self.clock.tick(60)
        # remove player data after confirmation
        try:
            p = player_path()
            if p.is_file():
                p.unlink()
        except Exception:
            pass

    def _draw(self) -> None:
        self.screen.fill((10, 10, 10))
        draw_text(self.screen, "ゲームオーバー", (SCREEN_WIDTH // 2 - 80, 180), self.title_font)
        draw_text(self.screen, "きみのモンスターは死んでしまった", (SCREEN_WIDTH // 2 - 180, 230), self.font)
        draw_text(self.screen, "エンターでタイトルへ", (SCREEN_WIDTH // 2 - 120, 280), self.font)


__all__ = ["GameOverScene"]
