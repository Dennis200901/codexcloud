"""Shared neon themed helpers for the 80s arcade experience."""

from __future__ import annotations

import math
import random
from functools import lru_cache
from typing import Iterable, Tuple

import pygame

Color = Tuple[int, int, int]


NEON_PURPLE: Color = (78, 0, 143)
NEON_PINK: Color = (255, 64, 160)
NEON_BLUE: Color = (30, 180, 255)
DEEP_SPACE: Color = (8, 10, 26)
STAR_COLOR: Color = (210, 220, 255)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


@lru_cache(maxsize=4)
def _gradient_surface(size: Tuple[int, int]) -> pygame.Surface:
    width, height = size
    surface = pygame.Surface(size)
    for y in range(height):
        t = y / max(height - 1, 1)
        color = (
            int(_lerp(DEEP_SPACE[0], NEON_PURPLE[0], t)),
            int(_lerp(DEEP_SPACE[1], NEON_PURPLE[1], t)),
            int(_lerp(DEEP_SPACE[2], NEON_PURPLE[2], t)),
        )
        pygame.draw.line(surface, color, (0, y), (width, y))
    return surface


_STARFIELD_CACHE: dict[Tuple[int, int], Iterable[Tuple[float, float, float]]] = {}


def _get_starfield(size: Tuple[int, int]) -> Iterable[Tuple[float, float, float]]:
    if size not in _STARFIELD_CACHE:
        random.seed(42 + size[0] * 7 + size[1] * 13)
        stars = []
        count = max(40, (size[0] * size[1]) // 15000)
        for _ in range(count):
            x = random.random()
            y = random.random() * 0.6
            radius = random.uniform(0.5, 1.5)
            stars.append((x, y, radius))
        _STARFIELD_CACHE[size] = stars
    return _STARFIELD_CACHE[size]


def draw_neon_background(surface: pygame.Surface) -> None:
    """Draw a stylised neon gradient with starfield and scrolling grid."""

    size = surface.get_size()
    surface.blit(_gradient_surface(size), (0, 0))

    time_seconds = pygame.time.get_ticks() / 1000.0

    star_surface = pygame.Surface(size, pygame.SRCALPHA)
    for sx, sy, radius in _get_starfield(size):
        x = int(sx * size[0])
        y = int(sy * size[1])
        pulse = 0.5 + 0.5 * math.sin(time_seconds * 2.5 + sx * 10)
        brightness = int(_lerp(120, 255, pulse))
        pygame.draw.circle(
            star_surface,
            (brightness, brightness, 255, 180),
            (x, y),
            max(1, int(radius * 2)),
        )
    surface.blit(star_surface, (0, 0), special_flags=pygame.BLEND_ADD)

    draw_neon_grid(surface)
    draw_scanlines(surface)


def draw_neon_grid(surface: pygame.Surface, spacing: int = 120) -> None:
    width, height = surface.get_size()
    grid_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    offset = (pygame.time.get_ticks() / 20) % spacing

    for x in range(-spacing, width + spacing, spacing):
        pygame.draw.line(
            grid_surface,
            (*NEON_BLUE, 70),
            (x + offset, height * 0.3),
            (x + offset, height),
            2,
        )

    for i in range(10):
        y = height * 0.3 + i * spacing * 0.18
        pygame.draw.line(
            grid_surface,
            (*NEON_PINK, max(20, 120 - i * 10)),
            (0, y + offset * 0.1),
            (width, y + offset * 0.1),
            2,
        )

    surface.blit(grid_surface, (0, 0), special_flags=pygame.BLEND_ADD)


def draw_scanlines(surface: pygame.Surface) -> None:
    width, height = surface.get_size()
    scan_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(0, height, 4):
        alpha = 35 if (y // 4) % 2 == 0 else 15
        pygame.draw.line(scan_surface, (0, 0, 0, alpha), (0, y), (width, y))
    surface.blit(scan_surface, (0, 0))


def draw_panel(surface: pygame.Surface, rect: pygame.Rect, title: str, lines: Iterable[str]) -> None:
    panel_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel_surface, (*NEON_BLUE, 120), panel_surface.get_rect(), border_radius=16)
    pygame.draw.rect(panel_surface, NEON_PINK, panel_surface.get_rect(), width=3, border_radius=16)
    surface.blit(panel_surface, rect.topleft)

    font = pygame.font.SysFont("arial", max(18, int(rect.height * 0.12)), bold=True)
    title_surface = font.render(title, True, (255, 255, 255))
    surface.blit(title_surface, (rect.x + 20, rect.y + 16))

    body_font = pygame.font.SysFont("arial", max(16, int(rect.height * 0.1)))
    offset_y = rect.y + 20 + title_surface.get_height()
    for line in lines:
        text_surface = body_font.render(line, True, (230, 240, 255))
        surface.blit(text_surface, (rect.x + 20, offset_y))
        offset_y += text_surface.get_height() + 6
