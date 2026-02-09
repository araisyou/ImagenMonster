import pygame
import shutil
from pathlib import Path
from tkinter import Tk, filedialog

from ..playercreate import save_default_player, load_player, save_player
from ..ui import draw_button, draw_text, fill_background
from ..constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from ..Imagegen import imagegen
from ..playercreate import load_player_chara
import json

PLAYER_DIR = Path(__file__).resolve().parents[2] / "Player"


class CreateScene:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock, font: pygame.font.Font, title_font: pygame.font.Font, on_created=None) -> None:
        self.screen = screen
        self.clock = clock
        self.font = font
        self.title_font = title_font
        self.on_created = on_created
        self.state = "start"  # start -> upload -> ready
        self.selected_image: Path | None = None
        btn_w, btn_h = 220, 60
        self.button_rect = pygame.Rect(0, 0, btn_w, btn_h)
        self.button_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40)

    def run(self) -> None:
        running = True
        while running:
            mouse_down = False
            mouse_pos = pygame.mouse.get_pos()
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_down = True
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            fill_background(self.screen)
            draw_text(self.screen, "モンスター作成", (SCREEN_WIDTH // 2 - 120, 120), self.title_font)
            if self.state == "start":
                draw_text(self.screen, "まずはあなたの相棒を作ろう", (SCREEN_WIDTH // 2 - 200, 200), self.font)
                if draw_button(self.screen, self.button_rect, "スタート", self.font, mouse_pos, mouse_down):
                    save_default_player()
                    self.state = "upload"
            elif self.state == "upload":
                draw_text(self.screen, "相棒のもとになる画像をちょうだい！", (SCREEN_WIDTH // 2 - 220, 200), self.font)
                btn_upload = self.button_rect.copy()
                btn_upload.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40)
                if draw_button(self.screen, btn_upload, "画像をアップロード", self.font, mouse_pos, mouse_down):
                    self._pick_image()
                if self.selected_image:
                    draw_text(self.screen, f"選択: {self.selected_image.name}", (SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 + 110), self.font)
                    btn_gen = self.button_rect.copy()
                    btn_gen.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 190)
                    if draw_button(self.screen, btn_gen, "作成！", self.font, mouse_pos, mouse_down):
                        self._generate_monster()
                        if self.on_created:
                            self.on_created()
                        running = False

            pygame.display.flip()

    def _pick_image(self) -> None:
        try:
            root = Tk()
            root.withdraw()
            path = filedialog.askopenfilename(filetypes=[("Image", "*.png;*.jpg;*.jpeg;*.webp;*.bmp")])
            root.update()
            root.destroy()
            if not path:
                return
            src = Path(path)
            dst_dir = PLAYER_DIR / "image" / "input"
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst = dst_dir / "input.png"
            shutil.copy(src, dst)
            self.selected_image = dst
        except Exception:
            self.selected_image = None

    def _generate_monster(self) -> None:
        # Mock generation: run imagegen (currently prints) and ensure output placeholders
        try:
            imagegen()
        except Exception:
            pass
        out_dir = PLAYER_DIR / "image" / "output"
        out_dir.mkdir(parents=True, exist_ok=True)
        # ensure 6 placeholder images exist
        for name in ["larva_front.png", "larva_back.png", "adult_front.png", "adult_back.png", "final_front.png", "final_back.png"]:
            path = out_dir / name
            if not path.exists():
                surf = pygame.Surface((256, 256))
                surf.fill((50, 80, 120))
                pygame.image.save(surf, path)
        out_json = PLAYER_DIR / "output.json"
        if not out_json.exists():
            skills = []
            try:
                skill_data = json.loads((PLAYER_DIR / "skill.json").read_text(encoding="utf-8"))
                skills = list(skill_data.keys())[:3]
            except Exception:
                skills = ["スキル1", "スキル2", "スキル3"]
            stub = {"hp": 30, "attack": 5, "defense": 5, "agility": 5, "skill": skills}
            out_json.write_text(json.dumps(stub, ensure_ascii=False, indent=2), encoding="utf-8")
        # reflect to Player.json
        try:
            data = load_player() or {}
            out = json.loads(out_json.read_text(encoding="utf-8"))
            data["hp"] = int(out.get("hp", data.get("hp", 10)))
            data["max_hp"] = int(out.get("hp", data.get("max_hp", out.get("hp", 10))))
            data["attack"] = int(out.get("attack", data.get("attack", 3))) + 5
            data["defense"] = int(out.get("defense", data.get("defense", 1))) + 3
            data["agility"] = int(out.get("agility", data.get("agility", 1))) + 3
            skills_out = out.get("skill") or []
            if isinstance(skills_out, list):
                data["skill"] = [str(s) for s in skills_out]
            elif skills_out not in ("", None):
                data["skill"] = [str(skills_out)]
            data.setdefault("evo", 1)
            save_player(data)
        except Exception:
            pass


__all__ = ["CreateScene"]
