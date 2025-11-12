"""Graphical Pac-Man front-end implemented with pygame."""
from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass
from importlib import import_module
from importlib.util import find_spec
from typing import Any, Dict, Tuple

if __package__ in (None, ""):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from pacman.common import DIRECTIONS, PacmanLogic
else:
    from .common import DIRECTIONS, PacmanLogic


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TILE_SIZE = 24
STATUS_HEIGHT = 96
STEP_DURATION = 0.12  # Seconds per simulation step
RESPAWN_PAUSE = 1.0   # Seconds to pause after losing a life


@dataclass(frozen=True)
class Palette:
    background: Tuple[int, int, int] = (0, 0, 0)
    wall: Tuple[int, int, int] = (33, 33, 222)
    pellet: Tuple[int, int, int] = (255, 191, 0)
    power: Tuple[int, int, int] = (255, 255, 255)
    pacman: Tuple[int, int, int] = (255, 232, 0)
    text: Tuple[int, int, int] = (255, 255, 255)
    frightened: Tuple[int, int, int] = (0, 174, 255)
    ghosts: Tuple[Tuple[int, int, int], ...] = (
        (255, 64, 64),
        (255, 184, 222),
        (255, 184, 82),
        (64, 255, 215),
    )


def _load_pygame():
    spec = find_spec("pygame")
    if spec is None:
        raise ModuleNotFoundError(
            "The Pac-Man GUI requires the 'pygame' package. Install it with 'pip install pygame'."
        )
    return import_module("pygame")


def _build_key_map(pg: Any) -> Dict[int, Tuple[int, int]]:
    return {
        pg.K_UP: DIRECTIONS["UP"],
        pg.K_DOWN: DIRECTIONS["DOWN"],
        pg.K_LEFT: DIRECTIONS["LEFT"],
        pg.K_RIGHT: DIRECTIONS["RIGHT"],
        pg.K_w: DIRECTIONS["UP"],
        pg.K_s: DIRECTIONS["DOWN"],
        pg.K_a: DIRECTIONS["LEFT"],
        pg.K_d: DIRECTIONS["RIGHT"],
    }


PACMAN_DIRECTION_ANGLE = {
    DIRECTIONS["RIGHT"]: 0,
    DIRECTIONS["DOWN"]: 90,
    DIRECTIONS["LEFT"]: 180,
    DIRECTIONS["UP"]: 270,
}


class PacmanRenderer:
    """Draws the Pac-Man world using pygame primitives."""

    def __init__(self, pg, screen, palette: Palette) -> None:
        self.pg = pg
        self.screen = screen
        self.palette = palette
        self.font = pg.font.SysFont("arial", 24)
        self.small_font = pg.font.SysFont("arial", 18)
        self.mouth_phase = 0.0

    def draw_world(self, logic: PacmanLogic, tile_size: int, status_height: int, delta: float) -> None:
        self.screen.fill(self.palette.background)
        self._draw_maze(logic, tile_size)
        self._draw_pellets(logic, tile_size)
        self._draw_characters(logic, tile_size, delta)
        self._draw_status_panel(logic, tile_size, status_height)

    # ------------------------------------------------------------------
    def _draw_maze(self, logic: PacmanLogic, tile_size: int) -> None:
        for row, col in logic.walls:
            rect = self.pg.Rect(col * tile_size, row * tile_size, tile_size, tile_size)
            self.pg.draw.rect(self.screen, self.palette.wall, rect, border_radius=6)

    def _draw_pellets(self, logic: PacmanLogic, tile_size: int) -> None:
        half = tile_size // 2
        pellet_radius = max(2, tile_size // 8)
        power_radius = max(4, tile_size // 4)

        for row, col in logic.pellets:
            center = (col * tile_size + half, row * tile_size + half)
            self.pg.draw.circle(self.screen, self.palette.pellet, center, pellet_radius)

        for row, col in logic.power_pellets:
            center = (col * tile_size + half, row * tile_size + half)
            self.pg.draw.circle(self.screen, self.palette.power, center, power_radius)

    def _draw_characters(self, logic: PacmanLogic, tile_size: int, delta: float) -> None:
        self._draw_ghosts(logic, tile_size)
        self._draw_pacman(logic, tile_size, delta)

    def _draw_pacman(self, logic: PacmanLogic, tile_size: int, delta: float) -> None:
        # Simple mouth animation that opens and closes based on time.
        self.mouth_phase = (self.mouth_phase + delta * 6) % (2 * math.pi)
        openness = (math.sin(self.mouth_phase) + 1) / 2  # 0..1
        openness = 0.15 + 0.35 * openness  # keep a minimum wedge so pacman is visible

        row, col = logic.pacman.position
        center_x = col * tile_size + tile_size // 2
        center_y = row * tile_size + tile_size // 2
        radius = tile_size // 2 - 2
        self.pg.draw.circle(self.screen, self.palette.pacman, (center_x, center_y), radius)

        angle = math.radians(PACMAN_DIRECTION_ANGLE.get(logic.pacman.direction, 0))
        gap = math.pi * openness
        points = [
            (center_x, center_y),
            (
                center_x + radius * math.cos(angle - gap),
                center_y + radius * math.sin(angle - gap),
            ),
            (
                center_x + radius * math.cos(angle + gap),
                center_y + radius * math.sin(angle + gap),
            ),
        ]
        self.pg.draw.polygon(self.screen, self.palette.background, [(round(x), round(y)) for x, y in points])

    def _draw_ghosts(self, logic: PacmanLogic, tile_size: int) -> None:
        for index, ghost in enumerate(logic.ghosts):
            row, col = ghost.position
            x = col * tile_size
            y = row * tile_size
            color = self.palette.frightened if ghost.frightened() else self._ghost_color(index)

            head_center = (x + tile_size // 2, y + tile_size // 2)
            head_radius = tile_size // 2 - 2
            self.pg.draw.circle(self.screen, color, head_center, head_radius)

            body_rect = self.pg.Rect(x + 2, y + tile_size // 2, tile_size - 4, tile_size // 2)
            self.pg.draw.rect(self.screen, color, body_rect)

            fringe_radius = max(2, tile_size // 8)
            for i in range(4):
                fringe_center = (x + fringe_radius * (2 * i + 1), y + tile_size - fringe_radius)
                self.pg.draw.circle(self.screen, color, fringe_center, fringe_radius)

            eye_offset_x = tile_size // 6
            eye_offset_y = tile_size // 6
            eye_radius = max(2, tile_size // 8)
            pupil_radius = max(2, tile_size // 16)
            for offset in (-eye_offset_x, eye_offset_x):
                eye_center = (head_center[0] + offset, head_center[1] - eye_offset_y)
                self.pg.draw.circle(self.screen, (255, 255, 255), eye_center, eye_radius)
                self.pg.draw.circle(self.screen, (0, 0, 0), eye_center, pupil_radius)

    def _ghost_color(self, index: int) -> Tuple[int, int, int]:
        palette = self.palette.ghosts
        return palette[index % len(palette)]

    def _draw_status_panel(self, logic: PacmanLogic, tile_size: int, status_height: int) -> None:
        panel_rect = self.pg.Rect(0, logic.height * tile_size, logic.width * tile_size, status_height)
        self.pg.draw.rect(self.screen, (16, 16, 16), panel_rect)

        score = self.font.render(f"Score: {logic.score}", True, self.palette.text)
        lives = self.font.render(f"Lives: {logic.lives}", True, self.palette.text)
        pellets = self.small_font.render(
            f"Pellets remaining: {logic.remaining_pellets()}", True, self.palette.text
        )
        instructions = self.small_font.render(
            "Arrows/WASD to move · ESC to quit · Enter to restart", True, self.palette.text
        )

        self.screen.blit(score, (16, logic.height * tile_size + 12))
        self.screen.blit(lives, (16, logic.height * tile_size + 44))
        self.screen.blit(pellets, (16, logic.height * tile_size + 70))
        self.screen.blit(
            instructions,
            (
                int(panel_rect.width / 2 - instructions.get_width() / 2),
                logic.height * tile_size + status_height - 28,
            ),
        )

    def draw_overlay(self, message: str, width: int, height: int) -> None:
        overlay = self.pg.Surface((width, height), self.pg.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        title = self.font.render(message, True, self.palette.text)
        prompt = self.small_font.render("Press Enter to play again", True, self.palette.text)
        self.screen.blit(title, (int(width / 2 - title.get_width() / 2), int(height / 2 - 40)))
        self.screen.blit(prompt, (int(width / 2 - prompt.get_width() / 2), int(height / 2)))


class PacmanApp:
    """Event loop and high-level orchestration for the pygame front-end."""

    def __init__(self) -> None:
        pg = _load_pygame()
        self.pg = pg
        self.key_map = _build_key_map(pg)

        pg.init()
        pg.display.set_caption("Pac-Man")
        pg.font.init()

        self.logic = PacmanLogic()
        self.tile_size = TILE_SIZE
        self.width = self.logic.width * self.tile_size
        self.height = self.logic.height * self.tile_size + STATUS_HEIGHT
        self.screen = pg.display.set_mode((self.width, self.height))

        self.renderer = PacmanRenderer(pg, self.screen, Palette())
        self.clock = pg.time.Clock()

        self.running = True
        self.state = "playing"  # "playing" or "gameover"
        self.game_over_message = ""
        self.step_accumulator = 0.0
        self.pause_timer = 0.0

    # ------------------------------------------------------------------
    def handle_events(self) -> None:
        for event in self.pg.event.get():
            if event.type == self.pg.QUIT:
                self.running = False
                return
            if event.type == self.pg.KEYDOWN:
                self._handle_keydown(event.key)

    def _handle_keydown(self, key: int) -> None:
        if key == self.pg.K_ESCAPE or key in (self.pg.K_q, self.pg.K_x):
            self.running = False
            return

        if self.state == "gameover" and key in (self.pg.K_RETURN, self.pg.K_SPACE):
            self.reset_game()
            return

        if self.state != "playing":
            return

        direction = self.key_map.get(key)
        if direction:
            self.logic.set_desired_direction(direction)

    # ------------------------------------------------------------------
    def update(self, delta: float) -> None:
        if self.state != "playing":
            return

        if self.pause_timer > 0:
            self.pause_timer = max(0.0, self.pause_timer - delta)
            return

        self.step_accumulator += delta
        while self.step_accumulator >= STEP_DURATION:
            self.step_accumulator -= STEP_DURATION
            event = self.logic.tick()
            if event == "life_lost":
                self.pause_timer = RESPAWN_PAUSE
                break

        if not self.logic.is_alive():
            self._trigger_game_over("Game Over")
        elif self.logic.is_level_cleared():
            self._trigger_game_over("You Win!")

    def _trigger_game_over(self, message: str) -> None:
        self.state = "gameover"
        self.game_over_message = message

    # ------------------------------------------------------------------
    def draw(self, delta: float) -> None:
        self.renderer.draw_world(self.logic, self.tile_size, STATUS_HEIGHT, delta)
        if self.state == "gameover":
            self.renderer.draw_overlay(self.game_over_message, self.width, self.height)
        self.pg.display.flip()

    # ------------------------------------------------------------------
    def reset_game(self) -> None:
        self.logic = PacmanLogic()
        self.step_accumulator = 0.0
        self.pause_timer = 0.0
        self.state = "playing"
        self.game_over_message = ""

    # ------------------------------------------------------------------
    def run(self) -> None:
        while self.running:
            delta = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update(delta)
            self.draw(delta)
        self.pg.quit()


def main() -> None:
    try:
        PacmanApp().run()
    except ModuleNotFoundError as exc:
        print(exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
