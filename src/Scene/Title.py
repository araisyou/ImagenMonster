import pygame
from pathlib import Path
from typing import Callable, Optional

from ..ui import fill_background, draw_text
from ..constants import SCREEN_WIDTH, SCREEN_HEIGHT


class TitleScene:
    def __init__(
        self,
        screen: pygame.Surface,
        clock: pygame.time.Clock,
        font: pygame.font.Font,
        title_font: pygame.font.Font,
        on_game: Callable[[], None],
        on_ai: Callable[[], None],
    ) -> None:
        self.screen = screen
        self.clock = clock
        self.font = font
        self.title_font = title_font
        self.on_game = on_game
        self.on_ai = on_ai
        self.background: Optional[pygame.Surface] = self._load_background()

    def run(self) -> None:
        running = True
        while running:
            mouse_down = False
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.on_game()
                    return
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_down = True
            running = self._draw(mouse_pos, mouse_down)
            pygame.display.flip()
            self.clock.tick(60)

    def _draw(self, mouse_pos: tuple[int, int], mouse_down: bool) -> bool:
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            fill_background(self.screen)
        draw_text(self.screen, "ImageMonsters", (SCREEN_WIDTH // 2 - 110, 120), self.title_font)
        draw_text(self.screen, "エンターキーではじめる", (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT - 120), self.font)
        return True

    def _load_background(self) -> Optional[pygame.Surface]:
        path = Path(__file__).resolve().parents[2] / "assets" / "Title.png"
        if path.is_file():
            try:
                img = pygame.image.load(str(path)).convert()
                return pygame.transform.smoothscale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except pygame.error as exc:
                print(f"Failed to load title background {path}: {exc}")
        else:
            print(f"Title background not found at {path}")
        return None
