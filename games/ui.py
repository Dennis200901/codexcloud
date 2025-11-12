import pygame


class Button:
    def __init__(self, rect, text, font, callback, bg_color=(40, 40, 40), hover_color=(70, 70, 70), text_color=(255, 255, 255)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.callback = callback
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)


class BackButton(Button):
    def __init__(self, font, callback):
        size = font.get_height() * 2
        super().__init__((20, 20, size, font.get_height() + 20), "Zurück", font, callback, bg_color=(120, 30, 30), hover_color=(160, 40, 40))

    def draw(self, surface):
        super().draw(surface)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=8)
