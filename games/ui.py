from __future__ import annotations

import math
from typing import Callable, Tuple

import pygame

from .theme import NEON_BLUE, NEON_PINK


class Button:
    """Simple neon styled button widget."""

    def __init__(
        self,
        rect: Tuple[float, float, float, float],
        text: str,
        font: pygame.font.Font,
        callback: Callable[[], None],
        bg_color=NEON_BLUE,
        hover_color=NEON_PINK,
        text_color=(255, 255, 255),
    ):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.callback = callback
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, surface: pygame.Surface) -> None:
        color = self.hover_color if self.is_hovered else self.bg_color

        glow_rect = self.rect.inflate(32, 24)
        glow_surface = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(glow_surface, (*color, 80), glow_surface.get_rect(), border_radius=18)
        surface.blit(glow_surface, glow_rect.topleft, special_flags=pygame.BLEND_ADD)

        border_rect = self.rect.inflate(8, 8)
        pygame.draw.rect(surface, (*color, 160), border_rect, border_radius=16)
        pygame.draw.rect(surface, (15, 15, 30), self.rect, border_radius=14)

        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 400.0)
        text_color = tuple(min(255, int(c * (0.7 + 0.3 * pulse))) for c in self.text_color)
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)


class BackButton(Button):
    def __init__(self, font: pygame.font.Font, callback: Callable[[], None]):
        width = max(180, font.get_height() * 4)
        height = font.get_height() + 26
        super().__init__((30, 30, width, height), "Zurück", font, callback)

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        pygame.draw.rect(surface, (255, 255, 255), self.rect.inflate(8, 8), 2, border_radius=16)
