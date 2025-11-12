import sys
from typing import Callable, Optional

import pygame

from games.chess import ChessGame
from games.ludo import LudoGame
from games.tetris import TetrisGame
from games.tic_tac_toe import TicTacToeGame
from games.ui import Button


class StartScreen:
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font, title_font: pygame.font.Font, launch_game: Callable[[str], None]):
        self.screen = screen
        self.font = font
        self.title_font = title_font
        self.launch_game = launch_game
        self.buttons: list[Button] = []
        self._create_buttons()

    def _create_buttons(self):
        labels = [
            ("Tetris", "tetris"),
            ("Tic Tac Toe", "tic_tac_toe"),
            ("Schach", "chess"),
            ("Mensch ärgere dich nicht", "ludo"),
        ]
        button_width = self.screen.get_width() * 0.4
        button_height = 80
        spacing = 30
        total_height = len(labels) * button_height + (len(labels) - 1) * spacing
        start_y = (self.screen.get_height() - total_height) / 2
        for i, (label, key) in enumerate(labels):
            rect = (
                (self.screen.get_width() - button_width) / 2,
                start_y + i * (button_height + spacing),
                button_width,
                button_height,
            )
            self.buttons.append(Button(rect, label, self.font, lambda k=key: self.launch_game(k)))

    def handle_events(self, events):
        for event in events:
            for button in self.buttons:
                button.handle_event(event)

    def update(self):
        pass

    def draw(self):
        self.screen.fill((12, 30, 50))
        title = self.title_font.render("Arcade Sammlung", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen.get_width() / 2, self.screen.get_height() * 0.2))
        self.screen.blit(title, title_rect)
        subtitle = self.font.render("Wähle ein Spiel", True, (200, 220, 255))
        sub_rect = subtitle.get_rect(center=(self.screen.get_width() / 2, title_rect.bottom + 60))
        self.screen.blit(subtitle, sub_rect)
        for button in self.buttons:
            button.draw(self.screen)
        hint = self.font.render("ESC zum Beenden", True, (200, 200, 200))
        hint_rect = hint.get_rect(center=(self.screen.get_width() / 2, self.screen.get_height() - 80))
        self.screen.blit(hint, hint_rect)


class GameApp:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        display_info = pygame.display.Info()
        self.screen = pygame.display.set_mode((display_info.current_w, display_info.current_h), pygame.FULLSCREEN)
        pygame.display.set_caption("Arcade Sammlung")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 42)
        self.title_font = pygame.font.SysFont("arial", 96, bold=True)
        self.current_screen: Optional[object] = None
        self.running = True
        self.start_screen = StartScreen(self.screen, self.font, self.title_font, self.launch_game)
        self.current_screen = self.start_screen

    def launch_game(self, key: str):
        def go_back():
            self.current_screen = self.start_screen

        if key == "tetris":
            self.current_screen = TetrisGame(self.screen, self.font, go_back)
        elif key == "tic_tac_toe":
            self.current_screen = TicTacToeGame(self.screen, self.font, go_back)
        elif key == "chess":
            self.current_screen = ChessGame(self.screen, self.font, go_back)
        elif key == "ludo":
            self.current_screen = LudoGame(self.screen, self.font, go_back)
        else:
            self.current_screen = self.start_screen

    def run(self):
        while self.running:
            events = [event for event in pygame.event.get()]
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.current_screen is not self.start_screen:
                        self.current_screen = self.start_screen
                    else:
                        self.running = False
            if self.current_screen:
                if hasattr(self.current_screen, "handle_events"):
                    self.current_screen.handle_events(events)
                if hasattr(self.current_screen, "update"):
                    self.current_screen.update()
                if hasattr(self.current_screen, "draw"):
                    self.current_screen.draw()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    GameApp().run()
