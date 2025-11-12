from typing import List

import pygame


NEON_PURPLE = (180, 60, 255)
NEON_BLUE = (45, 220, 255)
NEON_PINK = (255, 75, 180)
NEON_GLOW = (255, 255, 255)
DARK_SURFACE = (12, 16, 36)


class Button:
    def __init__(
        self,
        rect,
        text,
        font,
        callback,
        bg_color=NEON_PURPLE,
        hover_color=NEON_PINK,
        text_color=(15, 10, 35),
        accent_color=NEON_BLUE,
    ):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.callback = callback
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.accent_color = accent_color
        self.is_hovered = False
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def set_active(self, active: bool):
        self.active = active

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.bg_color
        if self.active:
            color = self.accent_color
        pygame.draw.rect(surface, DARK_SURFACE, self.rect.inflate(12, 12), border_radius=14)
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        if self.active or self.is_hovered:
            glow_rect = self.rect.inflate(8, 8)
            pygame.draw.rect(surface, self.accent_color, glow_rect, width=2, border_radius=12)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)


class BackButton(Button):
    def __init__(self, font, callback):
        size = font.get_height() * 2
        super().__init__(
            (20, 20, size, font.get_height() + 20),
            "Zurück",
            font,
            callback,
            bg_color=(120, 30, 60),
            hover_color=(180, 40, 80),
            text_color=(255, 240, 255),
            accent_color=(255, 120, 160),
        )

    def draw(self, surface):
        super().draw(surface)
        pygame.draw.rect(surface, NEON_GLOW, self.rect, 2, border_radius=12)


class OptionGroup:
    def __init__(self, rect, options, font, on_change, initial_index=0):
        self.rect = pygame.Rect(rect)
        self.options = options
        self.font = font
        self.on_change = on_change
        self.buttons: List[Button] = []
        button_width = self.rect.width / len(options)
        for idx, label in enumerate(options):
            btn_rect = (
                self.rect.x + idx * button_width + 10,
                self.rect.y,
                button_width - 20,
                self.rect.height,
            )
            button = Button(btn_rect, label, font, lambda i=idx: self.select(i))
            self.buttons.append(button)
        self.select(initial_index)

    def select(self, index: int):
        for idx, button in enumerate(self.buttons):
            button.set_active(idx == index)
        self.on_change(index)

    def handle_events(self, events):
        for event in events:
            for button in self.buttons:
                button.handle_event(event)

    def draw(self, surface):
        for button in self.buttons:
            button.draw(surface)
