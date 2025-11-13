"""Embedded Pac-Man screen for the arcade launcher."""

from __future__ import annotations

import math
from typing import Dict, Tuple

import pygame

from pacman import DIRECTIONS, PacmanLogic

from .theme import draw_neon_background, draw_panel, NEON_PINK
from .ui import BackButton


STEP_DURATION = 0.12
RESPAWN_PAUSE = 1.0

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


class PacmanGame:
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font, go_back):
        self.screen = screen
        self.font = font
        self.logic = PacmanLogic()
        self.small_font = pygame.font.SysFont("arial", max(18, font.get_height() - 12))
        self.back_button = BackButton(font, go_back)

        self.tile_size = self._calculate_tile_size()
        self.board_width = self.logic.width * self.tile_size
        self.board_height = self.logic.height * self.tile_size
        self.status_height = max(160, int(self.board_height * 0.25))
        total_height = self.board_height + self.status_height
        self.offset_x = (self.screen.get_width() - self.board_width) / 2
        self.offset_y = max(60, (self.screen.get_height() - total_height) / 2)

        self.state = "playing"
        self.game_over_message = ""
        self.step_accumulator = 0.0
        self.pause_timer = 0.0

    def _calculate_tile_size(self) -> int:
        max_width = self.screen.get_width() * 0.6
        max_height = self.screen.get_height() * 0.6
        tile_width = max_width / self.logic.width
        tile_height = max_height / self.logic.height
        return max(14, int(min(tile_width, tile_height)))

    def reset(self) -> None:
        self.logic.reset()
        self.state = "playing"
        self.game_over_message = ""
        self.step_accumulator = 0.0
        self.pause_timer = 0.0

    def handle_events(self, events) -> None:
        for event in events:
            self.back_button.handle_event(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset()
                elif self.state == "gameover" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.reset()
                elif self.state == "playing" and event.key in KEY_TO_DIRECTION:
                    self.logic.set_desired_direction(KEY_TO_DIRECTION[event.key])

    def update(self, delta: float = 0.0) -> None:
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
            self.game_over_message = "Level Geschafft!"

    def draw(self) -> None:
        draw_neon_background(self.screen)
        self._draw_maze()
        self._draw_pellets()
        self._draw_characters()
        self._draw_status_panel()
        self.back_button.draw(self.screen)

        if self.state == "gameover":
            self._draw_overlay(self.game_over_message)

    # Rendering helpers -------------------------------------------------
    def _tile_rect(self, row: int, col: int) -> pygame.Rect:
        return pygame.Rect(
            self.offset_x + col * self.tile_size,
            self.offset_y + row * self.tile_size,
            self.tile_size,
            self.tile_size,
        )

    def _draw_maze(self) -> None:
        for r in range(self.logic.height):
            for c in range(self.logic.width):
                rect = self._tile_rect(r, c)
                if (r, c) in self.logic.walls:
                    pygame.draw.rect(self.screen, (28, 28, 160), rect, border_radius=6)
                else:
                    pygame.draw.rect(self.screen, (10, 10, 40), rect, 1)

    def _draw_pellets(self) -> None:
        half = self.tile_size // 2
        for row, col in self.logic.pellets:
            center = (
                self.offset_x + col * self.tile_size + half,
                self.offset_y + row * self.tile_size + half,
            )
            pygame.draw.circle(self.screen, (255, 191, 0), center, max(2, self.tile_size // 8))
        for row, col in self.logic.power_pellets:
            center = (
                self.offset_x + col * self.tile_size + half,
                self.offset_y + row * self.tile_size + half,
            )
            radius = max(4, self.tile_size // 4)
            pygame.draw.circle(self.screen, (255, 255, 255), center, radius)

    def _draw_characters(self) -> None:
        self._draw_ghosts()
        self._draw_pacman()

    def _draw_pacman(self) -> None:
        row, col = self.logic.pacman.position
        center_x = self.offset_x + col * self.tile_size + self.tile_size // 2
        center_y = self.offset_y + row * self.tile_size + self.tile_size // 2
        radius = self.tile_size // 2 - 2
        pygame.draw.circle(self.screen, (255, 232, 0), (center_x, center_y), radius)

        angle = math.radians(DIRECTION_ANGLE.get(self.logic.pacman.direction, 0))
        gap = math.pi / 5
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
        pygame.draw.polygon(self.screen, (20, 20, 50), [(round(x), round(y)) for x, y in points])

    def _draw_ghosts(self) -> None:
        ghost_colors = [
            (255, 64, 64),
            (255, 184, 222),
            (255, 184, 82),
            (64, 255, 215),
        ]
        for index, ghost in enumerate(self.logic.ghosts):
            row, col = ghost.position
            x = self.offset_x + col * self.tile_size
            y = self.offset_y + row * self.tile_size
            color = (0, 174, 255) if ghost.frightened() else ghost_colors[index % len(ghost_colors)]

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

            for i in range(3):
                eye_center = (
                    head_center[0] - self.tile_size * 0.12 + i * self.tile_size * 0.12,
                    head_center[1] - self.tile_size * 0.1,
                )
                pygame.draw.circle(self.screen, (255, 255, 255), eye_center, max(2, self.tile_size // 10))
                pygame.draw.circle(
                    self.screen,
                    (20, 20, 60),
                    (
                        eye_center[0] + math.cos(math.radians(DIRECTION_ANGLE.get(ghost.direction, 0))) * self.tile_size * 0.05,
                        eye_center[1] + math.sin(math.radians(DIRECTION_ANGLE.get(ghost.direction, 0))) * self.tile_size * 0.05,
                    ),
                    max(1, self.tile_size // 16),
                )

    def _draw_status_panel(self) -> None:
        panel_width = self.board_width
        panel_rect = pygame.Rect(
            self.offset_x,
            self.offset_y + self.board_height + 24,
            panel_width,
            self.status_height - 24,
        )
        lines = [
            f"Score: {self.logic.score}",
            f"Level: {self.logic.level}",
            f"Leben: {self.logic.lives}",
            f"Restliche Punkte: {self.logic.remaining_pellets()}",
            "R = Neustart",
        ]
        draw_panel(self.screen, panel_rect, "Pac-Man", lines)

    def _draw_overlay(self, message: str) -> None:
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        title = self.font.render(message, True, (255, 255, 255))
        subtitle = self.small_font.render("ENTER oder SPACE für Neustart", True, NEON_PINK)
        title_rect = title.get_rect(center=(self.screen.get_width() / 2, self.screen.get_height() / 2 - 40))
        sub_rect = subtitle.get_rect(center=(self.screen.get_width() / 2, title_rect.bottom + 40))
        self.screen.blit(title, title_rect)
        self.screen.blit(subtitle, sub_rect)
