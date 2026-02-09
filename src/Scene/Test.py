import os
import re
import shutil
import pygame
from tkinter import Tk, filedialog

from .. import assets
from ..ImageToText import image_to_text, read_text_from_json
from ..constants import FPS
from ..ui import draw_button, draw_panel, draw_text, fill_background


class TestScene:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock, font: pygame.font.Font, title_font: pygame.font.Font) -> None:
        self.screen = screen
        self.clock = clock
        self.font = font
        self.title_font = title_font

        self.images, self.texts = self._load_assets_images()
        self.current_index = 0 if self.images else -1

        self.buttons = [
            {"text": "前へ", "rect": pygame.Rect(40, 520, 120, 44)},
            {"text": "次へ", "rect": pygame.Rect(180, 520, 120, 44)},
            {"text": "参照", "rect": pygame.Rect(320, 520, 120, 44)},
        ]

    def _load_assets_images(self) -> tuple[list[pygame.Surface], list[list[str]]]:
        loaded_images: list[pygame.Surface] = []
        loaded_texts: list[list[str]] = []
        assets_dir = os.path.join("assets", "images")
        max_size = (860, 400)  # パネル内に収まるようにする最大サイズ
        if not os.path.isdir(assets_dir):
            return loaded_images, loaded_texts
        for fname in sorted(os.listdir(assets_dir)):
            if fname.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                path = os.path.join(assets_dir, fname)
                loaded_images.append(assets.load_image(path, max_size))
                image_to_text(path)  # JSON生成（既存ならスキップ）
                loaded_texts.append(read_text_from_json(path))
        return loaded_images, loaded_texts

    def run(self) -> None:
        running = True
        while running:
            mouse_down = False
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_down = True

            fill_background(self.screen)
            self._draw_layout(mouse_pos, mouse_down)

            pygame.display.flip()
            self.clock.tick(FPS)

    def _draw_layout(self, mouse_pos: tuple[int, int], mouse_down: bool) -> None:
        draw_text(self.screen, "assets 内の画像ビューア", (30, 20), self.title_font)

        viewer_panel = pygame.Rect(30, 60, 900, 440)
        draw_panel(self.screen, viewer_panel)

        if self.current_index >= 0 and self.images:
            image = self.images[self.current_index]
            img_rect = image.get_rect(center=(viewer_panel.x + 280, viewer_panel.y + 220))
            self.screen.blit(image, img_rect)
            draw_text(
                self.screen,
                f"{self.current_index + 1} / {len(self.images)}",
                (viewer_panel.x + 12, viewer_panel.y + 12),
                self.font,
            )

            # テキスト情報を右側に表示
            info_x = viewer_panel.x + 520
            info_y = viewer_panel.y + 24
            for line in self.texts[self.current_index]:
                draw_text(self.screen, line, (info_x, info_y), self.font)
                info_y += 24
        else:
            draw_text(self.screen, "assets フォルダに画像がありません", viewer_panel.center, self.font)

        for idx, btn in enumerate(self.buttons):
            clicked = draw_button(
                self.screen,
                btn["rect"],
                btn["text"],
                self.font,
                mouse_pos,
                mouse_down,
            )
            if clicked:
                if idx == 0 and self.images:
                    self.current_index = (self.current_index - 1) % len(self.images)
                elif idx == 1 and self.images:
                    self.current_index = (self.current_index + 1) % len(self.images)
                elif idx == 2:
                    self._choose_and_add_image()

    def _choose_and_add_image(self) -> None:
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        filetypes = [
            ("Image files", ("*.png", "*.jpg", "*.jpeg", "*.webp")),
            ("All files", "*.*"),
        ]
        path = filedialog.askopenfilename(title="画像を選択", filetypes=filetypes)
        root.destroy()
        if not path:
            return
        # assets 配下に保存（参照順に image01, image02 ... の連番で命名）
        assets_dir = os.path.join("assets", "images")
        os.makedirs(assets_dir, exist_ok=True)

        ext = os.path.splitext(path)[1] or ".png"
        next_index = self._next_image_index(assets_dir)
        dest = os.path.join(assets_dir, f"image{next_index:02d}{ext}")
        try:
            shutil.copyfile(path, dest)
        except OSError:
            return

        max_size = (860, 400)
        new_image = assets.load_image(dest, max_size)
        image_to_text(dest)
        self.images.append(new_image)
        self.texts.append(read_text_from_json(dest))
        self.current_index = len(self.images) - 1

    def _next_image_index(self, assets_dir: str) -> int:
        pattern = re.compile(r"^image(\d+)\.[^.]+$")
        max_idx = 0
        for fname in os.listdir(assets_dir):
            m = pattern.match(fname.lower())
            if m:
                try:
                    num = int(m.group(1))
                    max_idx = max(max_idx, num)
                except ValueError:
                    continue
        return max_idx + 1
