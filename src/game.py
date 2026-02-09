import pygame

from .constants import SCREEN_HEIGHT, SCREEN_WIDTH
from .Scene.Title import TitleScene
from .Scene.Test import TestScene
from .Scene.Battle import BattleScene
from .Scene.Home import HomeScene
from .Scene.Create import CreateScene
from .Scene.GameOver import GameOverScene
from . import playercreate


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Image Viewer - Pygame")
        clock = pygame.time.Clock()

        # 日本語表示に対応したフォントを優先して取得（見つからなければデフォルト）
        jp_font_candidates = [
            "meiryo",
            "ms gothic",
            "msgothic",
            "yu gothic",
            "ms pgothic",
            "ms ui gothic",
            "arial unicode ms",
        ]
        font = pygame.font.SysFont(jp_font_candidates, 24)
        title_font = pygame.font.SysFont(jp_font_candidates, 32)

        self.scene = TitleScene(
            self.screen,
            clock,
            font,
            title_font,
            on_game=self._on_game,
            on_ai=self._on_ai,
        )
        self._clock = clock
        self._font = font
        self._title_font = title_font

    def run(self) -> None:
        self.scene.run()
        pygame.quit()

    def _on_game(self) -> None:
        print("start home")
        if playercreate.player_exists():
            self._start_home()
        else:
            self._start_create()

    def _start_battle(self) -> None:
        print("start battle")
        scene = BattleScene(self.screen, self._clock, self._font, self._title_font)
        scene.run()
        from .playercreate import load_player

        pdata = load_player() or {}
        hp = int(pdata.get("hp", 0)) if pdata else 0
        money = int(pdata.get("money", 0)) if pdata else 0
        if hp <= 0 and money <= 0:
            go = GameOverScene(self.screen, self._clock, self._font, self._title_font)
            go.run()
            # back to title after game over
            self.scene = TitleScene(
                self.screen,
                self._clock,
                self._font,
                self._title_font,
                on_game=self._on_game,
                on_ai=self._on_ai,
            )
            self.scene.run()
        else:
            self._start_home()

    def _start_home(self) -> None:
        scene = HomeScene(
            self.screen,
            self._clock,
            self._font,
            self._title_font,
            on_battle=self._start_battle,
        )
        scene.run()

    def _start_create(self) -> None:
        scene = CreateScene(
            self.screen,
            self._clock,
            self._font,
            self._title_font,
            on_created=self._start_home,
        )
        scene.run()

    def _on_ai(self) -> None:
        print("hello AI")
        # AIテストシーンに遷移
        scene = TestScene(self.screen, self._clock, self._font, self._title_font)
        scene.run()
