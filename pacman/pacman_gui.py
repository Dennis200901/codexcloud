"""Graphical Pac-Man clone rendered with pygame."""
from __future__ import annotations

import math
from typing import Dict, Tuple

import pygame

from pacman.common import DIRECTIONS, PacmanLogic

# --- Configuration -------------------------------------------------------
TILE_SIZE = 24
STATUS_HEIGHT = 96
STEP_DURATION = 0.12  # Seconds per simulation step
RESPAWN_PAUSE = 1.0   # Seconds to pause after losing a life

COLOR_BACKGROUND = (0, 0, 0)
COLOR_WALL = (33, 33, 222)
COLOR_PELLET = (255, 191, 0)
COLOR_POWER = (255, 255, 255)
COLOR_PACMAN = (255, 232, 0)
COLOR_TEXT = (255, 255, 255)
COLOR_FRIGHTENED = (0, 174, 255)
GHOST_COLORS = [
    (255, 64, 64),
    (255, 184, 222),
    (255, 184, 82),
    (64, 255, 215),
]

KEY_TO_DIRECTION: Dict[int, Tuple[int, int]] = {
    pygame.K_UP: DIRECTIONS["UP"],
    pygame.K_DOWN: DIRECTIONS["DOWN"],
    pygame.K_LEFT: DIRECTIONS["LEFT"],
    pygame.K_RIGHT: DIRECTIONS["RIGHT"],
    pygame.K_w: DIRECTIONS["UP"],
    pygame.K_s: DIRECTIONS["DOWN"],
    pygame.K_a: DIRECTIONS["LEFT"],
    pygame.K_d: DIRECTIONS["RIGHT"],
}

DIRECTION_ANGLE = {
    DIRECTIONS["RIGHT"]: 0,
    DIRECTIONS["DOWN"]: 90,
    DIRECTIONS["LEFT"]: 180,
    DIRECTIONS["UP"]: 270,
}


class PacmanApp:
    """Pygame application shell for the Pac-Man clone."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Pac-Man")
        pygame.font.init()

        self.logic = PacmanLogic()
        self.clock = pygame.time.Clock()
        self.tile_size = TILE_SIZE
        self.width = self.logic.width * self.tile_size
        self.height = self.logic.height * self.tile_size + STATUS_HEIGHT
        self.screen = pygame.display.set_mode((self.width, self.height))

        self.font = pygame.font.SysFont("arial", 24)
        self.small_font = pygame.font.SysFont("arial", 18)

        self.running = True
        self.state = "playing"  # "playing" or "gameover"
        self.game_over_message = ""
        self.step_accumulator = 0.0
        self.pause_timer = 0.0

    # --- Event handling --------------------------------------------------
    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif self.state == "gameover" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.reset_game()
                elif self.state == "playing":
                    if event.key in KEY_TO_DIRECTION:
                        self.logic.set_desired_direction(KEY_TO_DIRECTION[event.key])
                    elif event.key in (pygame.K_q, pygame.K_x):
                        self.running = False

    # --- Game state updates ----------------------------------------------
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
            self.state = "gameover"
            self.game_over_message = "Game Over"
        elif self.logic.is_level_cleared():
            self.state = "gameover"
            self.game_over_message = "You Win!"

    # --- Rendering -------------------------------------------------------
    def draw(self) -> None:
        self.screen.fill(COLOR_BACKGROUND)
        self._draw_maze()
        self._draw_pellets()
        self._draw_characters()
        self._draw_status_panel()

        if self.state == "gameover":
            self._draw_overlay(self.game_over_message)

        pygame.display.flip()

    def _draw_maze(self) -> None:
        for r in range(self.logic.height):
            for c in range(self.logic.width):
                if (r, c) in self.logic.walls:
                    rect = pygame.Rect(
                        c * self.tile_size,
                        r * self.tile_size,
                        self.tile_size,
                        self.tile_size,
                    )
                    pygame.draw.rect(self.screen, COLOR_WALL, rect, border_radius=6)

    def _draw_pellets(self) -> None:
        half = self.tile_size // 2
        for row, col in self.logic.pellets:
            center = (col * self.tile_size + half, row * self.tile_size + half)
            pygame.draw.circle(self.screen, COLOR_PELLET, center, self.tile_size // 8)
        for row, col in self.logic.power_pellets:
            center = (col * self.tile_size + half, row * self.tile_size + half)
            pygame.draw.circle(self.screen, COLOR_POWER, center, self.tile_size // 4)

    def _draw_characters(self) -> None:
        self._draw_ghosts()
        self._draw_pacman()

    def _draw_pacman(self) -> None:
        row, col = self.logic.pacman.position
        center_x = col * self.tile_size + self.tile_size // 2
        center_y = row * self.tile_size + self.tile_size // 2
        radius = self.tile_size // 2 - 2
        pygame.draw.circle(self.screen, COLOR_PACMAN, (center_x, center_y), radius)

        angle = DIRECTION_ANGLE.get(self.logic.pacman.direction, 0)
        mouth_angle = math.radians(angle)
        gap = math.pi / 4
        points = [
            (center_x, center_y),
            (
                center_x + radius * math.cos(mouth_angle - gap),
                center_y + radius * math.sin(mouth_angle - gap),
            ),
            (
                center_x + radius * math.cos(mouth_angle + gap),
                center_y + radius * math.sin(mouth_angle + gap),
            ),
        ]
        pygame.draw.polygon(
            self.screen,
            COLOR_BACKGROUND,
            [(round(x), round(y)) for x, y in points],
        )

    def _draw_ghosts(self) -> None:
        for index, ghost in enumerate(self.logic.ghosts):
            row, col = ghost.position
            x = col * self.tile_size
            y = row * self.tile_size
            color = COLOR_FRIGHTENED if ghost.frightened() else GHOST_COLORS[index % len(GHOST_COLORS)]

            head_center = (
                x + self.tile_size // 2,
                y + self.tile_size // 2,
            )
            head_radius = self.tile_size // 2 - 2
            pygame.draw.circle(self.screen, color, head_center, head_radius)

            body_rect = pygame.Rect(
                x + 2,
                y + self.tile_size // 2,
                self.tile_size - 4,
                self.tile_size // 2,
            )
            pygame.draw.rect(self.screen, color, body_rect)

            fringe_radius = self.tile_size // 8
            for i in range(4):
                fringe_center = (
                    x + fringe_radius * (2 * i + 1),
                    y + self.tile_size - fringe_radius,
                )
                pygame.draw.circle(self.screen, color, (int(fringe_center[0]), int(fringe_center[1])), fringe_radius)

            eye_offset_x = self.tile_size // 6
            eye_offset_y = self.tile_size // 6
            eye_radius = self.tile_size // 8
            pupil_radius = max(2, self.tile_size // 16)
            for offset in (-eye_offset_x, eye_offset_x):
                eye_center = (head_center[0] + offset, head_center[1] - eye_offset_y)
                pygame.draw.circle(self.screen, (255, 255, 255), eye_center, eye_radius)
                pygame.draw.circle(self.screen, (0, 0, 0), eye_center, pupil_radius)

    def _draw_status_panel(self) -> None:
        panel_rect = pygame.Rect(0, self.logic.height * self.tile_size, self.width, STATUS_HEIGHT)
        pygame.draw.rect(self.screen, (16, 16, 16), panel_rect)

        score_text = self.font.render(f"Score: {self.logic.score}", True, COLOR_TEXT)
        lives_text = self.font.render(f"Lives: {self.logic.lives}", True, COLOR_TEXT)
        remaining_text = self.small_font.render(
            f"Pellets remaining: {self.logic.remaining_pellets()}", True, COLOR_TEXT
        )
        instructions_text = self.small_font.render(
            "Use arrows or WASD to move · Press ESC to quit · Enter to restart", True, COLOR_TEXT
        )

        self.screen.blit(score_text, (16, self.logic.height * self.tile_size + 12))
        self.screen.blit(lives_text, (16, self.logic.height * self.tile_size + 44))
        self.screen.blit(remaining_text, (16, self.logic.height * self.tile_size + 70))
        self.screen.blit(
            instructions_text,
            (
                int(self.width / 2 - instructions_text.get_width() / 2),
                self.logic.height * self.tile_size + STATUS_HEIGHT - 28,
            ),
        )

    def _draw_overlay(self, message: str) -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        title = self.font.render(message, True, COLOR_TEXT)
        prompt = self.small_font.render("Press Enter to play again", True, COLOR_TEXT)
        self.screen.blit(
            title,
            (int(self.width / 2 - title.get_width() / 2), int(self.height / 2 - 40)),
        )
        self.screen.blit(
            prompt,
            (int(self.width / 2 - prompt.get_width() / 2), int(self.height / 2)),
        )

    # --- Game management -------------------------------------------------
    def reset_game(self) -> None:
        self.logic = PacmanLogic()
        self.state = "playing"
        self.game_over_message = ""
        self.step_accumulator = 0.0
        self.pause_timer = 0.0

    def run(self) -> None:
        while self.running:
            delta = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update(delta)
            self.draw()
        pygame.quit()


def main() -> None:
    PacmanApp().run()


if __name__ == "__main__":
    main()
